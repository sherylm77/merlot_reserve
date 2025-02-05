import sys
sys.path.append('../')
import tensorflow as tf
from pretrain.dataloader import encoder, load_and_resize_img, pad_to_fixed_size, get_shape_list, TOKEN_IS_VALID, filter_out_tokens_not_in_youtube, MASKAUDIO, MASK, MASKVIDEO, input_fn_builder, scatter_numpy, batch_index_iterator, sample_bernoulli, AUDIOSPAN
from copy import deepcopy
import functools
import numpy as np

def parse_record_singleimg(record, config):
    """
    Parse record for a single image task. Always including "id", "question", "label" and "answers"
    :param record:
    :param config:
    :return:
    """
    k2f = {
        'image_encoded': tf.io.FixedLenFeature((), tf.string, default_value=''),
        'id': tf.io.FixedLenFeature((), tf.string, default_value=''),
        'question': tf.io.VarLenFeature(tf.int64),
        'label': tf.io.FixedLenFeature((), tf.int64, 1),
    }
    for i in range(config['num_answers']):
        k2f[f'answer_{i}'] = tf.io.VarLenFeature(tf.int64)

    features = tf.io.parse_single_example(record, k2f)
    def _unsparsify(x):
        if isinstance(x, tf.SparseTensor):
            x = x.values
        if x.dtype == tf.int64:
            x = tf.cast(x, dtype=tf.int32)
        return x
    features = {k: _unsparsify(v) for k, v in features.items()}
    features['image'] = load_and_resize_img(features.pop('image_encoded'), config)
    return features


def preprocess_singleimg_linearqaoptions(record, config):
    """
    Process tasks with a single image and linear Q->A answering.

    Basically the answers get encoded as separate tensors
    :param record:
    :param config:
    :return:
    """
    features = parse_record_singleimg(record, config)

    q_with_mask = tf.concat([features['question'][:(config['lang_seq_len']-1)], [MASK]], 0)
    features['question'] = pad_to_fixed_size(q_with_mask, pad_value=0, output_shape=[config['lang_seq_len']])

    answers_concat = tf.concat([features[f'answer_{i}'] for i in range(config['num_answers'])], 0)
    answer_lens = [get_shape_list(features.pop(f'answer_{i}'))[0] for i in range(config['num_answers'])]
    answers = tf.RaggedTensor.from_row_lengths(answers_concat, row_lengths=answer_lens)

    answers = filter_out_tokens_not_in_youtube(answers)
    features['answers'] = pad_to_fixed_size(answers.to_tensor(), 0, output_shape=[config['num_answers'], config['text_span_length']], truncate=True, axis=1)
    return features


def preprocess_singleimg_jointoptions(record, config):
    """
    Process tasks with a single image and joint options (VCR the old way)
    :param record:
    :param config:
    :return:
    """
    features = parse_record_singleimg(record, config)

    if 'sep_token' in config:
        sep_tokens = encoder.encode(config['sep_token']).ids
        print("Separator tokens between Q and A: {}".format(encoder.decode(sep_tokens)), flush=True)
    else:
        sep_tokens = []

    answers = []
    for i in range(config['num_answers']):
        option_i = tf.concat([features['question'], sep_tokens, features.pop(f'answer_{i}')], 0)
        option_i = tf.concat([option_i[:(config['lang_seq_len']-1)], [MASK]], 0)
        answers.append(pad_to_fixed_size(option_i, pad_value=0, output_shape=[config['lang_seq_len']]))

    features['question'] = pad_to_fixed_size(features['question'], pad_value=0, output_shape=[config['lang_seq_len']])
    features['answers'] = tf.stack(answers, 0)
    return features


def preprocess_vcr(record, config):
    """
    Preprocess VCR -- basically here I'm doing Q,A and Q,A,R in a single call because that saves compute
    :param record:
    :param config:
    :return:
    """
    k2f = {
        'image': tf.io.FixedLenFeature((), tf.string, default_value=''),
        'image_fliplr': tf.io.FixedLenFeature((), tf.string, default_value=''),
        'id': tf.io.FixedLenFeature((), tf.string, default_value=''),
    }
    for prefix in ['qa', 'qar']:
        k2f[f'{prefix}_query'] = tf.io.VarLenFeature(tf.int64)
        for i in range(config['num_answers']):
            k2f[f'{prefix}_choice_{i}'] = tf.io.VarLenFeature(tf.int64)
        k2f[f'{prefix}_label'] = tf.io.FixedLenFeature((), tf.int64, 1)

    features = tf.io.parse_single_example(record, k2f)
    def _unsparsify(x):
        if isinstance(x, tf.SparseTensor):
            x = x.values
        if x.dtype == tf.int64:
            x = tf.cast(x, dtype=tf.int32)
        return x
    features = {k: _unsparsify(v) for k, v in features.items()}
    if config.get('do_random_scale', True):
        print("Randomly flipping image left/right", flush=True)
        image_encoded = tf.cond(
            sample_bernoulli(0.5),
            lambda: features.pop('image'),
            lambda: features.pop('image_fliplr'),
        )
    else:
        image_encoded = features.pop('image')
        del features['image_fliplr']

    features['image'] = load_and_resize_img(image_encoded, config)

    sep_tokens = {'qa': encoder.encode('answer: ').ids, 'qar': encoder.encode('rationale: ').ids}

    answers = []
    for prefix in ['qa', 'qar']:
        query = features.pop(f'{prefix}_query')
        for i in range(config['num_answers']):
            option_i = tf.concat([query, sep_tokens[prefix], features.pop(f'{prefix}_choice_{i}')], 0)
            option_i = tf.concat([option_i[:(config['lang_seq_len']-1)], [MASK]], 0)
            answers.append(pad_to_fixed_size(option_i, pad_value=0, output_shape=[config['lang_seq_len']]))

    features['answers'] = tf.reshape(tf.stack(answers, 0), [2, config['num_answers'], config['lang_seq_len']])
    features['labels'] = tf.stack([features.pop('qa_label'), features.pop('qar_label')], 0)
    return features

def get_mask_subset_with_prob(patched_input, prob):
    import math
    batch, seq_len, _ = patched_input.shape
    max_masked = math.ceil(prob * seq_len)

    rand = tf.random.uniform([batch, seq_len])
    _, sampled_indices = tf.math.top_k(rand, k=max_masked)

    new_mask = tf.zeros([batch, seq_len], tf.int32)
    with tf.compat.v1.Session() as sess:
        new_mask = scatter_numpy(new_mask.eval(), 1, sampled_indices.eval(), 1)
        sess.close()
    # new_mask = scatter_numpy(new_mask.numpy(), 1, sampled_indices.numpy(), 1)
    new_mask = tf.cast(new_mask, tf.bool)
    
    return new_mask

def prob_mask_like(t, prob):
    batch, seq_length, _ = t.shape
    x = tf.random.uniform([batch, seq_length], dtype=tf.float32) < prob
    return x

def preprocess_tvqa(record, config):
    """
    there are 7 frames, each with audio and associated text
    there is also an initial "frame" that doesn't have any image, but does have metadata where we stick the Q.
    :param record:
    :param config:
    :return:
    """
    k2f = {
        'id': tf.io.FixedLenFeature((), tf.string, default_value=''),
        'magic_number': tf.io.FixedLenFeature((), tf.float32, 1),
        'qa_query': tf.io.VarLenFeature(tf.int64),
        'answer_text': tf.io.VarLenFeature(tf.int64),
        'qa_label': tf.io.FixedLenFeature((), tf.int64, 1),
        'num_frames': tf.io.FixedLenFeature((), tf.int64, 1),
    }
    for i in range(config['num_answers']):
        k2f[f'qa_choice_{i}'] = tf.io.VarLenFeature(tf.int64)

    for i in range(config['num_segments']):
        k2f[f'c{i:02d}/image_encoded'] = tf.io.FixedLenFeature((), tf.string, default_value='')
        k2f[f'c{i:02d}/bmasks_encoded'] = tf.io.FixedLenFeature((), tf.string, default_value='')
        k2f[f'c{i:02d}/fmasks_encoded'] = tf.io.FixedLenFeature((), tf.string, default_value='')
        k2f[f'c{i:02d}/bbox'] = tf.io.VarLenFeature(tf.float32)
        k2f[f'c{i:02d}/fbbox'] = tf.io.VarLenFeature(tf.float32)
        k2f[f'c{i:02d}/spec_encoded'] = tf.io.FixedLenFeature((), tf.string, default_value='')
        k2f[f'c{i:02d}/sub'] = tf.io.VarLenFeature(tf.int64)
    features = tf.io.parse_single_example(record, k2f)
    def _unsparsify(x):
        if isinstance(x, tf.SparseTensor):
            x = x.values
        if x.dtype == tf.int64:
            x = tf.cast(x, dtype=tf.int32)
        return x
    

    segment_list = [{k: _unsparsify(features.pop(f'c{i:02d}/{k}')) for k in ['image_encoded', 'bmasks_encoded', 'fmasks_encoded', 'bbox', 'fbbox', 'spec_encoded', 'sub']} for i in
                    range(config['num_segments'])] # len(segment_list) = 7
    features = {k: _unsparsify(v) for k, v in features.items()} # dict_keys(['answer_text', 'qa_choice_0', 'qa_choice_1', 'qa_choice_2', 'qa_choice_3', 'qa_choice_4', 'qa_query', 'id', 'magic_number', 'num_frames', 'qa_label'])


    encodeds = tf.stack([x['image_encoded'] for x in segment_list]) # TensorShape([7])
    features['images'] = tf.map_fn(functools.partial(load_and_resize_img, config=config), elems=encodeds, fn_output_signature=tf.float32, name='decode_img') # TensorShape([7, 240, 768])
    
    bmask_encodeds = tf.stack([x['bmasks_encoded'] for x in segment_list]) # TensorShape([7])
    features['bmasks'] = tf.map_fn(functools.partial(load_and_resize_img, config=config), elems=bmask_encodeds, fn_output_signature=tf.float32, name='decode_img') # TensorShape([7, 240, 768])
    
    bbox = tf.ragged.stack([x['bbox'] for x in segment_list])
    
    fmask_encodeds = tf.stack([x['fmasks_encoded'] for x in segment_list]) # TensorShape([7])
    features['fmasks'] = tf.map_fn(functools.partial(load_and_resize_img, config=config), elems=fmask_encodeds, fn_output_signature=tf.float32, name='decode_img') # TensorShape([7, 240, 768])
    
    fbbox = tf.ragged.stack([x['fbbox'] for x in segment_list])
    
    if config['mask_where'] == "random":
        features['masks_info'], maskidx = create_masks(features["fmasks"], config, NO_MASK=True)
    else:
        mask_where = config['mask_where'][0]+'masks'
        if tf.reduce_sum(bbox.values) > 0.0:
            features['masks_info'], maskidx = create_masks(features[mask_where], config)
        else:
            features['masks_info'], maskidx = create_masks(features[mask_where], config, NO_MASK=True)

    audio_encodeds = tf.stack([x['spec_encoded'] for x in segment_list]) # TensorShape([7])
    features['audio_clips'] = tf.map_fn(functools.partial(tf.image.decode_jpeg, channels=1), audio_encodeds, fn_output_signature=tf.uint8) # TensorShape([7, 180, 65, 1])
    features['audio_clips'] = tf.reshape(features['audio_clips'], [config['num_segments'], 3, 60, 65]) # TensorShape([7, 3, 60, 65])
    features['audio_clips'] = tf.cast(features['audio_clips'], dtype=tf.float32) / features['magic_number'] # features['magic_number'] = 67.1942, TensorShape([7, 3, 60, 65])
    
    
    #############
    query = tf.concat([features.pop('qa_query'), encoder.encode('answer: ').ids], 0) # TensorShape([23])
    textonly_seqs = []
    audio_seqs = []
    vision_seqs_audio = []
    vision_seqs_text = []
    num_answer = 1
    
    for i in range(config['num_answers']):
        temp = features.pop(f'qa_choice_{i}')
    
    for i in range(num_answer):
        option_i = tf.concat([query, features.pop('answer_text')], 0) # TensorShape([26])
        # option_i = tf.concat([option_i[:(config['lang_seq_len'] - 1)], [MASK]], 0)

        # Now we add the subtitles
        sub_input_ragged = tf.ragged.stack([option_i[:(config['lang_seq_len'] - 1)]] + [x['sub'] for x in segment_list]) # TensorShape([8, None])
        segment_id = tf.cast(tf.where(sub_input_ragged)[:, 0], dtype=tf.int32) # TensorShape([109])
        textonly_seq_i = tf.stack([sub_input_ragged.values, segment_id], -1) # TensorShape([109, 2])
        textonly_seq_i = pad_to_fixed_size(textonly_seq_i, 0, output_shape=[config['lang_seq_len'], 2], truncate=True) # TensorShape([160, 2])
        textonly_seqs.append(textonly_seq_i)
        last_seqment_id_text = segment_id[-1]

        # Now we add the non-subtitles
        audio_span_full = tf.fill([3 * config['audio_token_length']], AUDIOSPAN) # TensorShape([18])
        audio_input_ragged = tf.ragged.stack([option_i[:(config['lang_seq_len'] - 1)]] + [audio_span_full for _ in segment_list]) # TensorShape([8, None])
        segment_id = tf.cast(tf.where(audio_input_ragged)[:, 0], dtype=tf.int32) # TensorShape([166])
        audio_seq_i = tf.stack([audio_input_ragged.values, segment_id], -1) # TensorShape([166, 2])
        audio_seq_i = pad_to_fixed_size(audio_seq_i, 0, output_shape=[config['lang_seq_len'], 2], truncate=True) # TensorShape([160, 2])
        audio_seqs.append(audio_seq_i)
        last_seqment_id_audio = segment_id[-1]

        h1, w1 = config['output_grid']
        vision_span_full = tf.fill([(h1*w1) // 4], MASKVIDEO) # TensorShape([18*30])
        vision_span_full_values = tf.where(maskidx, MASK, MASKVIDEO)
        
        vision_input_ragged = tf.ragged.stack([vision_span_full for _ in segment_list]) # TensorShape([8, None])
        segment_id_audio = tf.cast(tf.where(vision_input_ragged)[:, 0], dtype=tf.int32) + last_seqment_id_audio + 1
        segment_id_text = tf.cast(tf.where(vision_input_ragged)[:, 0], dtype=tf.int32) + last_seqment_id_text + 1
        
        vision_seq_i_audio = tf.stack([vision_span_full_values, segment_id_audio], -1) 
        vision_seq_i_text = tf.stack([vision_span_full_values, segment_id_text], -1) 
        
        vision_seq_i_audio = tf.concat([audio_seq_i, vision_seq_i_audio], 0)
        vision_seq_i_text = tf.concat([textonly_seq_i, vision_seq_i_text], 0)
        vision_seqs_audio.append(vision_seq_i_audio)
        vision_seqs_text.append(vision_seq_i_text)

    features['textonly_seqs'] = tf.stack(textonly_seqs) # TensorShape([1, 160, 2])
    features['audio_seqs'] = tf.stack(audio_seqs) # TensorShape([1, 160, 2])
    features['vision_seqs_audio'] = tf.stack(vision_seqs_audio) # (1, 580, 2)
    features['vision_seqs_text'] = tf.stack(vision_seqs_text) # (1, 580, 2)
    features['labels'] = features.pop('qa_label') # <tf.Tensor: shape=(), dtype=int32, numpy=1>

    # do this so we don't have to mask
    frame_is_valid = tf.cast(tf.less(tf.range(config['num_segments']), features['num_frames']), dtype=tf.float32)
    features['images'] *= frame_is_valid[:, None, None] # frame_is_valid[:, None, None] -> TensorShape([7, 1, 1]); TensorShape([7, 240, 768])
    features['bmasks'] *= frame_is_valid[:, None, None]
    features['fmasks'] *= frame_is_valid[:, None, None]

    if config.get('do_random_scale', True):
        print("Random adjustment of audio clips")
        old_shape = get_shape_list(features['audio_clips'], 4) # [7, 3, 60, 65]
        old_nwindow = old_shape[0] * old_shape[1] * old_shape[2] # 1260
        num_mels = old_shape[3] # 65

        features['audio_clips'] = features['audio_clips'][:features['num_frames']] # TensorShape([7, 3, 60, 65])
        giant_seq = tf.reshape(features['audio_clips'], [-1, num_mels]) # TensorShape([1260, 65])
        avg = tf.reduce_mean(giant_seq, 0) # TensorShape([65])
        std = tf.math.reduce_std(giant_seq, 0) # TensorShape([65])

        amt_to_pad_start = 4
        start = tf.random.normal([amt_to_pad_start, num_mels], mean=avg, stddev=std) # TensorShape([4, 65])

        amt_to_pad_end = 4 + (old_nwindow - get_shape_list(giant_seq, 2)[0]) # 4
        end = tf.random.normal([amt_to_pad_end, num_mels], mean=avg, stddev=std) # TensorShape([4, 65])

        seq = tf.concat([start, giant_seq, end], 0) # TensorShape([1268, 65])
        start_idx = tf.random.uniform([], minval=0, maxval=amt_to_pad_start + 1, dtype=tf.int32) # 3
        seq = seq[start_idx:(start_idx+old_nwindow)] # TensorShape([1260, 65])
        features['audio_clips'] = tf.reshape(seq, old_shape) # TensorShape([7, 3, 60, 65])
    
    features['audio_clips'] *= frame_is_valid[:, None, None, None] # TensorShape([7, 3, 60, 65])

    # final thing should always be 1 and it's being rounded right now
    features['audio_clips'] = tf.concat([features['audio_clips'][..., :-1],
                                              tf.ones_like(features['audio_clips'][..., 0, None])
                                              ], -1) # tf.ones_like(features['audio_clips'][..., 0, None]) -> (7, 3, 60, 1); features['audio_clips'][..., :-1] -> (7, 3, 60, 64); TensorShape([7, 3, 60, 65])
    
    return features


def pad_up_to(t, max_in_dims, constant_values):
    s = tf.shape(t)
    paddings = [[0, m-s[i]] for (i,m) in enumerate(max_in_dims)]
    return tf.pad(t, paddings, 'CONSTANT', constant_values=constant_values)

def tf_random_choice_no_replacement_v1(one_dim_input, num_indices_to_drop):
    input_length = tf.shape(one_dim_input)[0]
    tf.random.set_seed(123456)
    uniform_distribution = tf.random.uniform(
        shape=[input_length],
        minval=0,
        maxval=None,
        dtype=tf.float32,
        seed=10,
        name=None
    )

    # grab the indices of the greatest num_words_to_drop values from the distibution
    _, indices_to_keep = tf.nn.top_k(uniform_distribution, num_indices_to_drop)
    sorted_indices_to_keep = tf.sort(indices_to_keep)

    # gather indices from the input array using the filtered actual array
    result = tf.gather(one_dim_input, sorted_indices_to_keep)
    return result

def create_masks(mask, config, NO_MASK = False):
    # import pdb; pdb.set_trace()
    *batch_dims, hw, pp3 = mask.shape
    output_grid_h, output_grid_w = config['output_grid']
    h2 = output_grid_h // config['vit_pooling_ratio'] # 9
    w2 = output_grid_w // config['vit_pooling_ratio'] # 15
    b2 = int(np.prod(list(batch_dims) + [h2])) # 63
    
    if NO_MASK:
        tf.random.set_seed(123456)
        seq_mask = tf.random.uniform([b2 * w2], minval=0, maxval=4, dtype=tf.int32, seed=10)
        seq = tf.range(b2 * w2, dtype=tf.int32)
        return tf.stack([seq, seq_mask], -1), tf.cast(tf.ones([b2 * w2], tf.int32), dtype=tf.bool)
    
    total_bmask = 0.25 * config['alpha']
    mseq = tf.reshape(mask, [b2, config['vit_pooling_ratio'], w2, config['vit_pooling_ratio'], config['hidden_size']]) # (63,2,15,2,768)
    mseq = tf.transpose(mseq, [0, 2, 1, 3, 4]) #mseq.swapaxes(-4, -3) # (63,15,2,2,768)
    mseq = tf.reshape(mseq, [b2 * w2, config['vit_pooling_ratio'] ** 2, config['hidden_size']]) # (945,4,768)
    mseq_wo_hd = tf.reduce_sum(mseq, -1) # (945, 4)
    ragged_mseq = tf.RaggedTensor.from_tensor(mseq_wo_hd, padding=0) # (945, None)
    mrow = tf.cast(tf.where(ragged_mseq)[:, 0], dtype=tf.int32)
    mcol = tf.cast(tf.where(ragged_mseq)[:, 1], dtype=tf.int32)
    midx = tf.stack([mrow, mcol], -1)
    p1, p2 = mseq.shape[0], mseq.shape[1]
    midx = midx[:int(p1*p2*total_bmask)]
    midx_shape = get_shape_list(midx)
    mseq_wo_hd = tf.tensor_scatter_nd_update(tf.zeros_like(mseq_wo_hd, dtype=tf.float32), midx, tf.ones([midx_shape[0]], dtype=tf.float32))
    percent_masks = midx_shape[0] / (p1 * p2)
    suremask = tf.cast(tf.reduce_sum(mseq_wo_hd, -1), dtype=tf.bool)

    if percent_masks < 0.25:
        remidxn = int((0.25 - percent_masks) * p1 * p2)
        allidx = tf.math.logical_not(suremask)
        allidx = tf.cast(tf.where(allidx), dtype=tf.int32)
        remidx = tf_random_choice_no_replacement_v1(tf.reshape(allidx, [-1]), remidxn)
        suremask = tf.tensor_scatter_nd_update(suremask, remidx[:, None], tf.cast(tf.ones([remidxn], tf.int32), dtype=tf.bool))
        tf.random.set_seed(123456)
        seq_mask = tf.random.uniform([get_shape_list(remidx)[0]], minval=0, maxval=4, dtype=tf.int32, seed=10)#[..., None]
        remidx = tf.stack([remidx, seq_mask], -1)
        midx = tf.concat([midx, remidx], 0)
   
    midx =  pad_to_fixed_size(midx, -1, output_shape=[p1, 2], truncate=True)
    return midx, suremask

def make_dataset_singleimg(config, fns, preprocessor, batch_size, num_devices=1, is_training=True):
    """
    :param config:
    :param fns:
    :param batch_size:
    :param num_devices:
    :param is_training:
    :return:
    """
    merged_config = deepcopy(config['data'])
    merged_config.update(config['model'])

    print(f"Constructing TFRecord Input FN over {fns}", flush=True)
    num_parallel_reads = min(len(fns), 4) if isinstance(fns, list) else None
    if not is_training:
        num_parallel_reads = 1

    dataset = tf.data.TFRecordDataset(fns, num_parallel_reads=num_parallel_reads)

    options = tf.data.Options()
    options.threading.private_threadpool_size = 48
    options.threading.max_intra_op_parallelism = 1
    options.experimental_optimization.map_parallelization = True
    options.experimental_deterministic = True #(not is_training)
    dataset = dataset.with_options(options)

    ### EDITTED HERE TO REMOVE DATA SHUFFLE
    # if is_training:
    #     dataset = dataset.shuffle(buffer_size=256)
    ### END

    dataset = dataset.map(functools.partial(preprocessor, config=merged_config),
                          num_parallel_calls=tf.data.experimental.AUTOTUNE)
    dataset = dataset.batch(batch_size=batch_size, drop_remainder=is_training)
    def _handle_batch(batched_tensor):
        for k in batched_tensor.keys():
            batched_tensor[k] = tf.reshape(batched_tensor[k],
                                           [num_devices, batch_size // num_devices] +
                                           get_shape_list(batched_tensor[k])[1:])
            if (merged_config['use_bfloat16']) and batched_tensor[k].dtype == tf.float32:
                batched_tensor[k] = tf.cast(batched_tensor[k], dtype=tf.bfloat16)
        return batched_tensor
    dataset = dataset.map(_handle_batch)
    return dataset

def finetune_input_fn_builder(config, preprocessor_type):
    preprocessor = {
        'singleimg_linearqaoptions': preprocess_singleimg_linearqaoptions,
        'singleimg_jointoptions': preprocess_singleimg_jointoptions,
        'vcr': preprocess_vcr,
        'tvqa': preprocess_tvqa,
    }[preprocessor_type]

    ds_train_iter = input_fn_builder(config, make_dataset_fn=functools.partial(make_dataset_singleimg, preprocessor=preprocessor))
    for batch in ds_train_iter:
        id_ = batch.pop('id')
        yield id_, batch

def finetune_val_input_fn_builder(config, preprocessor_type):
    preprocessor = {
        'singleimg_linearqaoptions': preprocess_singleimg_linearqaoptions,
        'singleimg_jointoptions': preprocess_singleimg_jointoptions,
        'vcr': preprocess_vcr,
        'tvqa': preprocess_tvqa,
    }[preprocessor_type]

    import jax
    from flax import jax_utils

    current_host = jax.process_index()
    num_devices = jax.local_device_count()
    batch_size = config['device']['batch_size']

    matching_fns = []
    for i in range(config['data']['num_val_files']):
        matching_fns.append(config['data']['val_fns'].format(i))

    dataset = tf.data.TFRecordDataset(matching_fns, num_parallel_reads=None)

    options = tf.data.Options()
    options.threading.private_threadpool_size = 48
    options.threading.max_intra_op_parallelism = 1
    options.experimental_optimization.map_parallelization = True
    options.experimental_deterministic = True
    dataset = dataset.with_options(options)

    merged_config = deepcopy(config['data'])
    merged_config.update(config['model'])
    merged_config['do_random_scale'] = False

    dataset = dataset.map(functools.partial(preprocessor, config=merged_config),
                          num_parallel_calls=tf.data.experimental.AUTOTUNE)
    dataset = dataset.batch(batch_size=batch_size, drop_remainder=False)
    def _bfloat16_cast(batched_tensor):
        for k in batched_tensor.keys():
            if (merged_config['use_bfloat16']) and batched_tensor[k].dtype == tf.float32:
                batched_tensor[k] = tf.cast(batched_tensor[k], dtype=tf.bfloat16)
        return batched_tensor
    dataset = dataset.map(_bfloat16_cast)

    for item in dataset:
        item = jax.tree_map(lambda x: x._numpy(), item)

        ids = [id.decode('utf-8') for id in item.pop('id').tolist()]
        pad_val = batch_size - len(ids)

        if pad_val > 0:
            print("Padding final batch by {}".format(batch_size - len(ids)), flush=True)
            for i in range(pad_val):
                ids.append('pad')

        for k in item.keys():
            if pad_val > 0:
                pad_shape = [pad_val] + list(item[k].shape[1:])
                item[k] = np.concatenate([item[k], np.zeros(pad_shape, item[k].dtype)], 0)
            item[k] = item[k].reshape([num_devices, batch_size // num_devices] + list(item[k].shape[1:]))

        yield ids, item
        
        
if __name__ == '__main__':
    
    import yaml

    with open('../pretrain/configs/base.yaml', 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    merged_config = deepcopy(config['data'])
    merged_config.update(config['model'])
    config = merged_config
    
    config['num_train_files'] = 256
    config['num_answers'] = 5
    config['random_scale_max'] = 1.1
    config['random_scale_min'] = 1.0
    config['num_segments'] = 7
    config['mask_where'] = "face"
    config['alpha'] = 0.1

    
    dataset = tf.data.TFRecordDataset(['/data/sakter/preprocessed/out/train245of256.tfrecord'])
    # # For eager debugging
    for record in dataset:
        x = preprocess_tvqa(record, config)
    
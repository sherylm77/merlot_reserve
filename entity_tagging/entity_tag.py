import nltk
from nltk.tree import Tree
from nltk.corpus import wordnet as wn

def find_noun_phrases(tree):
    return [subtree for subtree in tree.subtrees(lambda t: t.label()=='NP')]

def find_head_of_np(np):
    noun_tags = ['NN', 'NNS', 'NNP', 'NNPS']
    top_level_trees = [np[i] for i in range(len(np)) if type(np[i]) is Tree]
    ## search for a top-level noun
    top_level_nouns = [t for t in top_level_trees if t.label() in noun_tags]
    if len(top_level_nouns) > 0:
        ## if you find some, pick the rightmost one, just 'cause
        return top_level_nouns[-1][0]
    else:
        ## search for a top-level np
        top_level_nps = [t for t in top_level_trees if t.label()=='NP']
        if len(top_level_nps) > 0:
            ## if you find some, pick the head of the rightmost one, just 'cause
            return find_head_of_np(top_level_nps[-1])
        else:
            ## search for any noun
            nouns = [p[0] for p in np.pos() if p[1] in noun_tags]
            if len(nouns) > 0:
                ## if you find some, pick the rightmost one, just 'cause
                return nouns[-1]
            else:
                ## return the rightmost word, just 'cause
                return np.leaves()[-1]
            
def get_np_chunked_text(input_text):
    tokenized_text = nltk.word_tokenize(input_text)
    tuples = nltk.pos_tag(tokenized_text)

    grammar = r""" 
                PP: {<IN><DT>?<JJ>*<PRP|NN|NNS|NNP|NNPS>}
                NP: {<DT>?<JJ>*<PRP|NN|NNS|NNP|NNPS> | <NP><PP>}
                """

    cp = nltk.RegexpParser(grammar, loop=2) 
    result = cp.parse(tuples)
#     result.draw()
    return str(result)

# get raw sentence without parens and tree structure
def get_sent_from_tree(phrase_tree):
    phrase = str(phrase_tree)
    words = []
    for word in phrase.split():
        if "/" in word:
            words.append(word.split("/")[0])
    return ' '.join(words)

def get_unique(noun_phrases):
    unique_np = []
    redundant = []
    sent_noun_phrases = [get_sent_from_tree(phrase) for phrase in noun_phrases]

    for np in sent_noun_phrases:
        for np2 in sent_noun_phrases:
            if np not in np2:
                if (np,sent_noun_phrases.index(np))  not in unique_np and np not in redundant:
                    unique_np.append((np, sent_noun_phrases.index(np)))
            else:
                if np != np2 and np not in redundant:
                    redundant.append(np)

    unique_np = [noun_phrases[i] for (np,i) in unique_np]

    return unique_np

# returns head of given noun phrase
def get_head_nouns(chunked_text):
    tree = Tree.fromstring(chunked_text)
    # print(tree)
    heads = []
    heads_with_phrases = []
    for np in get_unique(find_noun_phrases(tree)):
        # print("noun phrase:", " ".join(np.leaves()))
        head = find_head_of_np(np)
        # print("head:", head)
        heads.append(head)
        heads_with_phrases.append((head, np))
    return heads, heads_with_phrases

def is_human(noun):
    categories = wn.synsets(noun.split("/")[0])
    if categories != []:
        category = categories[0]
        person_hypernym = wn.synset('person.n.01') in category.lowest_common_hypernyms(wn.synset('person.n.01'))
    else:
        person_hypernym = False
    is_pronoun = "PRP" in noun
    return person_hypernym or is_pronoun

def get_human_entities(input_text):
    tree_text = get_np_chunked_text(input_text)
    nouns, nouns_with_phrases = get_head_nouns(tree_text)
    human_entities = []
    for (noun, phrase) in nouns_with_phrases:
        # print("noun:", noun, "human:", is_human(noun))
        if (is_human(noun)):
            human_entities.append((noun, phrase))
    return human_entities

# puts angle brackets <> around noun phrases whose heads are human
def get_human_entities_in_place(input_text):
    entities_with_phrases = get_human_entities(input_text)
    human_entities = [x.split("/")[0] for (x,y) in entities_with_phrases]
    text_with_entities_marked = input_text
    for (noun, phrase) in entities_with_phrases:
        phrase_raw = get_sent_from_tree(phrase)
        if phrase_raw in input_text:
            text_with_entities_marked = text_with_entities_marked.replace(phrase_raw, "<"+phrase_raw+">", 1)
    return text_with_entities_marked

input_text = "The old man from India finally talked to him."
print(get_human_entities_in_place(input_text))
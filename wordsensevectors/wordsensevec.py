import nltk
# nltk.download('wordnet')
# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
from nltk.corpus import wordnet as wn
import numpy as np
from numpy import dot
from numpy import average
from numpy.linalg import norm
import os


def load_glove_vectors(glove_file):
    f = open(glove_file, 'r')
    vectors = {}
    for line in f:
        split_line = line.split()
        word = split_line[0]
        embedding = np.array([float(val) for val in split_line[1:]])
        vectors[word] = embedding
    f.close()
    return vectors


cosine_sim_threshold = 0.05


def get_word_sense_vectors(candidate):
    vectors = {}
    try:
        candidate_vec = glove[candidate]
    except Exception:
        print(candidate, "not found in glove")
        return None
    for ss in wn.synsets(candidate):
        # if candidate == "bank":
            # print("synonym of ", candidate, " is ", ss.lemmas()[0].name())
            # print("key of ", candidate, " is ", ss.lemmas()[0].key())
        tokens = nltk.word_tokenize(ss.definition())
        pos_tags = nltk.pos_tag(tokens)
        word_vectors = []
        for gloss_pos, tag in pos_tags:
            #if tag == 'VBD' or tag == 'NN' or tag == 'ADJ' or tag == 'ADV':
            try:
                gloss_word_vec = glove[gloss_pos]
            except Exception:
                print(gloss_pos, "not found in glove")
                continue
            cos_sim = dot(gloss_word_vec, candidate_vec) / (norm(gloss_word_vec) * norm(candidate_vec))
            if cos_sim > cosine_sim_threshold:
                word_vectors.append(gloss_word_vec)
        if len(word_vectors) == 0:
            continue
        sense_vector = average(word_vectors)
        vectors[ss] = sense_vector
    return vectors


def disambiguate_word_sense(word, context_vector):
    vectors = sense_vectors_collection[word]
    if len(vectors) == 0:
        return None
    cos_sims = {}
    for sense, sense_vector in vectors.items():
        cos_sim = dot(context_vector, sense_vector) / (norm(context_vector) * norm(sense_vector))
        cos_sims[sense] = cos_sim
    sorted_list = sorted(cos_sims.items(), key=lambda x: x[1])
    if len(sorted_list) == 0:
        return None
    nearest_sense = sorted_list.pop()[0]
    return nearest_sense


glove = load_glove_vectors(
    '/media/iftekhar/New Volume/Personal/Admission Docs/Germany/RWTH/MI/Lab - AI_Language_Technology/training_nball47634/glove.6B.50d.txt')

sense_vectors_collection = {}


def find_wn_key(sentence, lookup_word):
    sorted_sense_vectors_collection = {}
    pos = []
    pos_vectors = {}
    tokens_input = nltk.word_tokenize(sentence)
    pos_tags_input = nltk.pos_tag(tokens_input)
    for word, pos_tag in pos_tags_input:
        # print(word, "is tagged as", pos_tag)
        # if pos_tag == 'VBD' or pos_tag == 'NN' or pos_tag == 'ADJ' or pos_tag == 'ADV':
        try:
            pos_vectors[word] = glove[word]
            pos.append(word)
        except Exception:
            print(pos, " not found in glove")
    for p in pos:
        sense_vectors = get_word_sense_vectors(p)
        if sense_vectors is None:
            continue
        sense_vectors_collection[p] = sense_vectors
        sorted_sense_vectors_collection[p] = len(sense_vectors)
    # S2C sorting for content word
    sorted_sense_vectors_collection = sorted(sorted_sense_vectors_collection.items(), key=lambda x: x[1])
    # print("sorted by sense count", sorted_sense_vectors_collection)
    # Context vector initialization
    context_vec = average(list(pos_vectors.values()))
    wn_key = "nf"
    for w, _ in sorted_sense_vectors_collection:
        nearest_sense = disambiguate_word_sense(w, context_vec)
        if nearest_sense is None:
            continue
        if w == lookup_word:
            wn_key = nearest_sense.lemmas()[0].key()
            break
        nearest_word = nearest_sense.lemmas()[0].name()
        try:
            pos_vectors[nearest_word] = glove[nearest_word]
            # print(w, "is replaced with", nearest_word)
            # print(nearest_word, "has sense key", nearest_sense.lemmas()[0].key())
            if nearest_word != w:
                pos_vectors.pop(w)
            context_vec = average(list(pos_vectors.values()))
        except Exception:
            print(nearest_word, " not found in glove")
            continue
    # print(pos_vectors.keys())
    sense_vectors_collection.clear()
    return wn_key


for dirpath,_,filenames in os.walk("/home/iftekhar/Desktop/gold/Annotated_Sentences/"):
    if len(filenames) == 0:
        continue
    for file in filenames:
        f = open(os.path.join(dirpath, file), 'r', encoding='ISO-8859-1')
        from itertools import islice
        for line in islice(f, 1):
            split_line = line.split('?')
            metadata_array = split_line[0].split(' ')
            linkup_key = metadata_array[0]
            lookup_word = metadata_array[2]
            sentence = split_line[1].split(' ', 2)[2]
            print("|" + linkup_key + "|     " + find_wn_key(sentence, lookup_word))

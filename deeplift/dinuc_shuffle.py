from collections import defaultdict
from random import shuffle


#compile the dinucleotide edges
def prepare_edges(s):
    edges = defaultdict(list)
    for i in xrange(len(s)-1):
        edges[s[i]].append(s[i+1])
    return edges


def shuffle_edges(edges):
    #for each character, remove the last edge, shuffle, add edge back
    for char in edges:
        last_edge = edges[char][-1]
        edges[char] = edges[char][:-1]
        the_list = edges[char]
        shuffle(the_list)
        edges[char].append(last_edge)
    return edges


def traverse_edges(s, edges):
    generated = [s[0]]
    edges_queue_pointers = defaultdict(lambda: 0)
    for i in range(len(s)-1):
        last_char = generated[-1]
        generated.append(edges[last_char][edges_queue_pointers[last_char]])
        edges_queue_pointers[last_char] += 1
    return "".join(generated)

def dinuc_shuffle(s, pad_lengths = None):
    if pad_lengths == None:
        s = s.upper()
        return traverse_edges(s, shuffle_edges(prepare_edges(s)))
    else:
        s = s.upper()
        left_pad = pad_lengths[0]
        right_pad = pad_lengths[1]
        seq = s[left_pad : len(s) - right_pad]
        shuffled_seq = transverse_edges(seq, shuffle_edges(prepare_edges(seq)))
        return s[:left_pad] + shuffled_seq + s[(len(s) - right_pad):]

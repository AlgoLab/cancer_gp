""" The :mod:`dollo_node_operators` module contains ovolutionary operators
for DolloNode individuals.

"""
import copy
import random

from functools import lru_cache 

from bitstring import BitArray

from anytree import search

from read_element import ReadElement

def assign_reads_to_dollo_tree(root, reads):
    """ Assigns all the reads to the closest nodes in the tree,
    respectively.
    
    Args:
         root (DolloNode): root of the tree to whose nodes reads should be assigned.
         reads (list): list of the reads that should be assigned to various nodes 
                  in the tree.
     
    Returns:            
        list that contains two components: 
            1) list of the asignments  - list of pairs (node, read);
            2) sum of the distances among reads and the closest nodes that
            are assigned to those reads respectively.
    
    Note:
        Function uses the func:`~DolloNode.closest_node_in_tree` function 
        from the :mod:`ga_node` module.
    """
    total_distance = 0
    complete_assignment = {}
    for read in reads:
        (node, d) = root.closest_node_in_tree( read )
        complete_assignment[read] = node
        total_distance += d
    return (complete_assignment, total_distance)    
    
    
def init_dollo_node_individual(ind_class, labels, k):
    """ Initialization of the individual.
    Args:
        ind_class: class of the individual to be initialized - should be 
            DolloNode.
        labels (list): list of the lables of the nodes in the tree that should 
            be initialized.
        k(int): Value od the Dollo k parameter.
    Returns: 
        DolloNode: individual that is initialized.           
    """
    rootBitArray = BitArray(int = 0, length = len(labels) )
    root = ind_class('--', rootBitArray)
    root.tree_initialize(labels, k)
    return root

@lru_cache(maxsize=8192, typed=True)
def dolo_closest_node_distance(individual, read):
    """ Finds the closest node within the tree for the given read, as well
        as distance betwwen that node and read.
    
    Args:
         individual (DoloNode): individual that represents root of the node.
         read : read that should be assigned to the node in the tree.

    Notes:    
        Node is the closest according to metrics that is induced with Hamming
        distance.
        This method consults informations about unknown reads (that are stored 
        in bitarry unknown_read) within read element. 
    """
    (c_n,d) = individual.closest_node_in_tree(read)
    return (c_n,d)

def dollo_evaluate_direct_level0(reads, alpha, individual):
    """ Evaluation of the individual. Doesnt't count false positives.

    Args:
         reads (list): list of the reads that should be assigned to various nodes 
                  in the tree.
         individual (DoloNode): individual that should be evaluated.
         alpha: probability of false positive
    Returns:            
         objection value of the individual to be evaluated.    
    """
    objection_value = 0
    for read in reads:
        (node, d) = dolo_closest_node_distance(individual,read)
        objection_value += d
    return objection_value

def dollo_evaluate_direct_level1(reads, alpha, individual):
    """ Evaluation of the individual. Takes into account false positives on
        one position.        

    Args:
         reads (list): list of the reads that should be assigned to various nodes 
                  in the tree.
         individual (DoloNode): individual that should be evaluated.
         alpha: probability of false positive
    Returns:            
         objection value of the individual to be evaluated.    
    """
    objection_value = dollo_evaluate_direct_level0(reads, alpha, individual)
    for read in reads:
        for i in range(0,read.binary_read.length):
            if( read.binary_read[i]):
                read2 = BitArray(read.binary_read)
                read2[i]=False
                re2 = ReadElement("XXX2", read2, read.unknown_read)
                (node, d) = dolo_closest_node_distance(individual,re2)
                objection_value += d * alpha
    return objection_value

def dollo_evaluate_direct_level2(reads, alpha, individual):
    """ Evaluation of the individual. Takes into account false positives on
        two positions.        
    Args:
         reads (list): list of the reads that should be assigned to various nodes 
                  in the tree.
         individual (DoloNode): individual that should be evaluated.
         alpha: probability of false positive
    Returns:            
         objection value of the individual to be evaluated.    
    """
    objection_value = dollo_evaluate_direct_level1(reads, alpha, individual)
    for read in reads:
        for i in range(0,read.binary_read.length):
            for j in range(i+1, read.binary_read.length):
                if( read.binary_read[i] and read.binary_read[j]):
                    read2 = BitArray(read.binary_read)
                    read2[i]=False
                    read2[j]=False
                    re2 = ReadElement("XXX2", read2, read.unknown_read)
                    (node, d) = dolo_closest_node_distance(individual,re2)
                    objection_value += d * alpha * alpha
    return objection_value


def dollo_evaluate_direct_level3(reads, alpha, individual):
    """ Evaluation of the individual. Takes into account false positives on
        three positions.        
    Args:
         reads (list): list of the reads that should be assigned to various nodes 
                  in the tree.
         individual (DoloNode): individual that should be evaluated.
         alpha: probability of false positive
    Returns:            
         objection value of the individual to be evaluated.    
    """
    objection_value = dollo_evaluate_direct_level2(reads, alpha, individual)
    for read in reads:
        for i in range(0,read.binary_read.length):
            for j in range(i+1, read.binary_read.length):
                for k in range(j+1, read.binary_read.length):
                    if( read.binary_read[i] and read.binary_read[j] and read.binary_read[k]):
                        read2 = BitArray(read.binary_read)
                        read2[i]=False
                        read2[j]=False
                        read2[k]=False
                        re2 = ReadElement("XXX2", read2, read.unknown_read)
                        (node, d) = dolo_closest_node_distance(individual,re2)
                        objection_value += d * alpha * alpha
    return objection_value

def evaluate_dollo_node_individual(reads, individual, alpha):
    """ Evaluation of the individual.

    Args:
         reads (list): list of the reads that should be assigned to various nodes 
                  in the tree.
         individual (DoloNode): individual that should be evaluated.
         alpha: probability of false positive
    Returns:            
        pair where first element is objection value of the individual to be
            evaluated.    
    """
    return (dollo_evaluate_direct_level2(reads, individual, alpha),)    

def set_consits_of_plus_lebels(list_of_sets):
    """ Ironing the list of sets and keeping only plus nodes.

    Args:
        list_of_sets (list): list of the set that is to be searched.
     
    Returns:            
        set of the plus labels in list
    """
    ret = {*[]}
    for s in list_of_sets:
        for x in s:
            if(x[-1]=='+'):
                ret.add(x)
    return ret

def sets_are_equal(set1,set2):
    """ Checks if sets are equal

    Args:
        set1 (set): first set for comparison.
        set2 (set): second set for comparison.
     
    Returns:            
        boolean that indicate equality of the sets
    """
    for x in set1:
        if( not x in set2):
            return False;
    for x in set2:
        if( not x in set1):
            return False;
    return True


def dollo_crossover_exchange_subtrees(labels,individual1,individual2):
    """ Crossover between two individuals, by exchanging its subtrees

    Args:
        labels (list): list of the lables of the nodes that exists in the tree.
        individual1 (DolloNode): first individual in crossover.
        individual2 (DolloNode): second individual in crossover.
     
    Returns:            
        pair where the first componet is indicator of succes and the second is
        individual that is mutated e.g. output of the mutation process.
    
    Notes:
        Subtrees that are exchanged should cover same plus nodes and subtrees 
        should not be same.
        Minus nodes will be set after exchanging.
    """
    if(individual1.tree_is_equal(individual2)):
        return(False,individual1,individual2)
    individual1_n = copy.deepcopy( individual1 )
    individual2_n = copy.deepcopy( individual2 )
    part1 = {}
    part1 = individual1_n.tree_get_partition(part1)
    part2 = {}
    part2 = individual2_n.tree_get_partition(part2)
    ret = False
    for lab in labels:
        lab += '+'
        if(not lab in part1):
            continue
        covered1 = part1[lab]
        set_covered1 = set_consits_of_plus_lebels(covered1)
        if(len(set_covered1)==0):
            continue
        if(not lab in part2):
            continue
        covered2 = part2[lab]
        set_covered2 = set_consits_of_plus_lebels(covered2)
        if(len(set_covered2)==0):
            continue
        if(not sets_are_equal(set_covered1,set_covered2)):
            continue
        node1 = search.find(individual1_n,lambda node: node.node_label == lab)
        node2 = search.find(individual2_n,lambda node: node.node_label == lab)
        print("**********************************************")
        print("* Begin in dollo_crossover_exchange_subtrees *")
        print(node1)
        print(part1)
        print(set_covered1)
        print(node2)
        print(part2)
        print(set_covered2)
        print("*   End in dollo_crossover_exchange_subtrees *")
        print("**********************************************")
        if(node1.tree_is_equal(node2)):
            continue
        # Cross over subtrees
        parent1 = node1.parent
        parent2 = node2.parent
        node1.parent = parent2
        node2.parent = parent1
        # Handling minus nodes in subtree roted with node1
        # TO DO
        # Compaction and regularization in subtree roted with node1
        node1.tree_compact_vertical()
        node1.tree_compact_horizontal()
        node1.tree_rearange_by_label()
        node1.tree_set_binary_tags(labels)
        # Handling minus nodes in subtree roted with node2
        # TO DO
        # Compaction and regularization in subtree roted with node2
        node2.tree_compact_vertical()
        node2.tree_compact_horizontal()
        node2.tree_rearange_by_label()
        node2.tree_set_binary_tags(labels)
        ret = True
        break
    return (ret,individual1_n,individual2_n)

def dollo_crossover_exchange_edge(labels,individual1,individual2):
    """ Crossover between two individuals, by exchanging one edge of each

    Args:
        labels (list): list of the lables of the nodes that exists in the tree.
        individual1 (DolloNode): first individual in crossover.
        individual2 (DolloNode): second individual in crossover.
     
    Returns:            
        pair where the first componet is indicator of succes and the second is
        individual that is mutated e.g. output of the mutation process.    
     """
    if(individual1.tree_is_equal(individual2)):
        return(False,individual1,individual2)
    individual1_n = copy.deepcopy(individual1)
    individual2_n = copy.deepcopy(individual2)
    random_label = random.choice(labels)
    random01 = random.random()
    label_is_plus = random01 < (len(labels)/float(1+len(individual1_n.descendants)) ) 
    if(label_is_plus):
        random_label += '+'
        node1 = search.find(individual1_n,lambda node: node.node_label == random_label)
        node2 = search.find(individual2_n,lambda node: node.node_label == random_label)
        print("******************************************")
        print("* Begin in dollo_crossover_exchange_edge *")
        print(random_label)
        print(node1.parent)
        print(node2.parent)
        print("*  End in dollo_crossover_exchange_edge  *")
        print("******************************************")
    else:
        random_label += '-'
        print("******************************************")
        print("* Begin in dollo_crossover_exchange_edge *")
        print(random_label)
        print("*  End in dollo_crossover_exchange_edge  *")
        print("******************************************")
    return (True,individual1_n,individual2_n)


def crossover_dollo_node_individuals(labels,individual1,individual2):
    """ Crossover between individual1 and individual2.
    
    Args:
         labels (list): list of the lables of the nodes that exists in the tree.
         individual1 (DolloNode): first individual in crossover.
         individual2 (DolloNode): second individual in crossover.
     
    Returns:            
        two-element tuple which contains offsprings e.g. output of the
        crossover process.
    """
    print("* Executing crossover step *")
    (success,individual1_new,individual2_new) = dollo_crossover_exchange_subtrees(
            labels,
            individual1, 
            individual2)
    if(success):
        return (individual1_new,individual2_new,)
    (success,individual1_new,individual2_new) = dollo_crossover_exchange_edge(
            labels,
            individual1, 
            individual2)
    if(success):
        return (individual1_new,individual2_new,)
    individual1n = copy.deepcopy( individual1 )
    individual2n = copy.deepcopy( individual2 )
    return (individual1n,individual2n)

def dollo_mutation_node_add(labels,k,individual):
    """ Mutation of the individual, by randomly adding one node

    Args:
        labels (list): list of the lables of the nodes in the tree that should 
            be initialized.
        k(int): Value od the Dollo k parameter.
         individual (DolloNode): individual that will be mutated.
     
    Returns:            
        pair where the first componet is indicator of succes and the second is
        individual that is mutated e.g. output of the mutation process.
    """
    individual_n = copy.deepcopy( individual )
    random_parent = random.choice(individual_n.descendants)
    random_label = random.choice(labels)
    random01 = random.random()
    label_is_plus = random01 < (len(labels)/float(1+len(individual_n.descendants)) ) 
    if(label_is_plus):
        # adding plus label and removing same plus label
        random_label += '+'
    else:
        # adding minus label and removing same plus label
        random_label += '-'
    return (False,individual_n)

def dollo_mutation_node_remove(labels, k, individual):
    """ Mutation of the individual, by randomly removing one node

    Args:
        labels (list): list of the lables of the nodes in the tree that should 
            be initialized.
        k(int): Value od the Dollo k parameter.
        individual (DolloNode): individual that will be mutated.
     
    Returns:            
        pair where the first componet is indicator of succes and the second is
        individual that is mutated e.g. output of the mutation process.
    """
    individual_n = copy.deepcopy( individual )
    return (False,individual_n)

def dollo_mutation_node_promote(labels, k, level, individual):
    """ Mutation of the individual, by randomly randomly selected node
        up to the tree for given level.

    Args:
        labels (list): list of the lables of the nodes in the tree that should 
            be initialized.
        k(int): Value od the Dollo k parameter.
        level (int): level for move
        individual (DolloNode): individual that will be mutated.
     
    Returns:            
        pair where the first componet is indicator of succes and the second is
        individual that is mutated e.g. output of the mutation process.
    """
    individual_n = copy.deepcopy( individual )
    return (False,individual_n)


def dollo_mutation_node_demote(labels, k, level, individual):
    """ Mutation of the individual, by randomly randomly selected node
        down to the tree for given level.

    Args:
        labels (list): list of the lables of the nodes in the tree that should 
            be initialized.
        k(int): Value od the Dollo k parameter.
        level (int): level for move
        individual (DolloNode): individual that will be mutated.
     
    Returns:            
        pair where the first componet is indicator of succes and the second is
        individual that is mutated e.g. output of the mutation process.
    """
    individual_n = copy.deepcopy( individual )
    return (False,individual_n)


def mutate_dollo_node_individual(labels, k, individual):
    """ Mutatuion of the individual.

    Args:
         individual (DolloNode): individual that will be mutated.
     
    Returns:            
        tuple where the first elelemt is mutataed e.g. output of the
        mutation process.
    """
    (success,individual_new) = dollo_mutation_node_add(labels, k, individual)
    if(success):
        return (individual_new,)
    else:
        individual_n = copy.deepcopy( individual )
        return (individual_n,)

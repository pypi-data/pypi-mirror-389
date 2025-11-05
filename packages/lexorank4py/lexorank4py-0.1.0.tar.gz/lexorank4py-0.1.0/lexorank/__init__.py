
BASE36 = "0123456789abcdefghijklmnopqrstuvwxyz"

'''convert a lexorank string(base36) to an integer'''
def rank_to_int(rank: str) -> int:
    return int(rank, 36)


'''convert an integer to a lexorank string(base36) with fixed length(used for initialization)'''
def int_to_rank_with_length(value: int, length: int) -> str:
    """    
    eg: 
    - int_to_rank_with_length(10, 2) -> "0a"
    - int_to_rank_with_length(35, 2) -> "0z"
    - int_to_rank_with_length(36, 2) -> "10"
    """
    if value < 0:
        raise ValueError("Value must be non-negative")
    
    if value == 0:
        result = "0"
    else:
        digits = []
        temp = value
        while temp > 0:
            temp, rem = divmod(temp, 36)
            digits.append(BASE36[rem])
        result = "".join(reversed(digits))
    # fill 0 at the left till the length is reached
    if len(result) < length:
        result = "0" * (length - len(result)) + result
    
    return result


'''convert an integer to a lexorank string(base36)'''
def int_to_rank(value: int) -> str:
    """    
    eg: 
    - int_to_rank_with_length(10, 2) -> "0a"
    - int_to_rank_with_length(35, 2) -> "0z"
    - int_to_rank_with_length(36, 2) -> "10"
    """
    if value < 0:
        raise ValueError("Value must be non-negative")
    
    if value == 0:
        result = "0"
    else:
        digits = []
        temp = value
        while temp > 0:
            temp, rem = divmod(temp, 36)
            digits.append(BASE36[rem])
        result = "".join(reversed(digits))
    
    return result


'''initialize the lexorank for a given number of items'''
def initialize_lexorank(num: int) -> list[str]:
  
    if num <= 0:
        return []
    
    if num < 35:
        rank_length = 1
        max_value = 35  
    else:
        rank_length = 2
        max_value = 36 ** 2 - 1  
    
    step = max_value // (num + 1)
    
    result = []
    for i in range(1, num + 1):
        value = i * step
        result.append(int_to_rank_with_length(value, rank_length))
    
    return result


'''pad the rank to the right with '0' to the length'''
def pad_right(rank: str, length: int) -> str:
    if len(rank) < length:
        rank_padded = rank + "0" * (length - len(rank))
    else:
        rank_padded = rank
    return rank_padded


'''get the rank between two ranks'''
def get_rank_between(left: str, right: str) -> str:
    # make the two ranks have the same length
    maxlen = max(len(left), len(right))
    left = pad_right(left, maxlen)
    right = pad_right(right, maxlen)

    if rank_to_int(right) - rank_to_int(left) <= 1:
        left += "0"
        right += "0"

    mid = (rank_to_int(left) + rank_to_int(right)) // 2
    
    return int_to_rank_with_length(mid, len(left))
    

'''get the rank before at the head'''
def get_rank_before(right:str) -> str:
    mid = (rank_to_int(right)) // 2
    return int_to_rank(mid)


'''get the rank after at the tail'''
def get_rank_after(left:str) -> str:
    tail = "z"*len(left)
    return get_rank_between(left, tail)

__all__ = [
    'rank_to_int',
    'int_to_rank_with_length',
    'int_to_rank',
    'initialize_lexorank',
    'pad_right',
    'get_rank_between',
    'get_rank_before',
    'get_rank_after',
]


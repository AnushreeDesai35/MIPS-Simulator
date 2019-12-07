class D_cache:

    def __init__(self, id, size):
        self.cache = [[], []]
        self.hit = False
        self.miss = False
        # for i in range(self.size):
        #     self.cache_block.append(Cache_Block(i, CACHE_BLOCK_SIZE))


    def cache_check(self, addr):
        block = int(addr/4)
        i_set = block % 2
        for b in self.cache[i_set]:
            if(addr in b):
                hit = True
            else:
                miss = True

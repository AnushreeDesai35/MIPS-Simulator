class D_cache:
    def __init__(self):
        self.cache = [[(1,2,3,4),(5,6,7,8)], []]

    def cache_check(self, addr):
        block = int(addr/4)
        i_set = block % 2
        for b in self.cache[i_set]:
            if(addr in b):
                hit = True
            else:
                miss = True

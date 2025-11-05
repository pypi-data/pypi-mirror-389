#pragma once
#include <vector>

namespace largebm {

class Pattern {
public:
    std::vector<int> seq;
    std::vector<unsigned long long> str_pnt;
    std::vector<int> list;
    unsigned long long freq = 0;

    Pattern() = default;
    Pattern(std::vector<int>& _seq, int item) {
        seq.swap(_seq);
        seq.push_back(item);
        freq = 0;
    }
    Pattern(int item) {
        seq.push_back(item);
        freq = 0;
    }
};

void Freq_miner();
void Freq_miner_list(const std::vector<std::vector<int>>& db,
                     std::vector<int>& prefix,
                     unsigned long long theta,
                     std::vector<std::vector<int>>& out);

extern unsigned long long int num_patt;
extern std::vector<bool> ilist;
extern std::vector<bool> slist;
extern std::vector<int>  DFS_numfound;
extern Pattern            _patt;

} // namespace largebm

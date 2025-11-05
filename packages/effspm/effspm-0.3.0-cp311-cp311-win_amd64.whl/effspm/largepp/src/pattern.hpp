#pragma once
#include <vector>

namespace largepp {

class Pattern {
public:
    std::vector<int> seq;
    std::vector<unsigned int> str_pnt;
    std::vector<unsigned long long> seq_ID;

    std::vector<int> slist;
    std::vector<int> ilist;

    unsigned long long freq;

    Pattern() : freq(0) {}

    explicit Pattern(int item) : freq(0) {
        seq.push_back(item);
    }

    Pattern(std::vector<int>& _seq, int item) : freq(0) {
        seq.reserve(_seq.size() + 1);
        for (int i = 0; i < static_cast<int>(_seq.size()); ++i)
            seq.push_back(_seq[i]);
        seq.push_back(item);
    }
};

} // namespace largepp

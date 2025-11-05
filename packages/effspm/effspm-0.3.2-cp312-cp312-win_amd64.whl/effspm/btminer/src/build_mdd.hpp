#pragma once

#include <vector>
#include <cmath>
#include "load_inst.hpp"

namespace btminer {

using std::vector;

void Build_MDD(vector<int>& items);

class Arc {
public:
    int chld = -1;
    int sibl = -1;
    int freq = 0;
    int anct;
    int itmset;
    int item;

    Arc(int _itm, int _itmset, int _anc)
        : chld(-1), sibl(-1), freq(0), anct(_anc), itmset(_itmset), item(_itm) {}

    // sometimes professor used this shorter ctor
    Arc(int _itm, int _anc)
        : chld(-1), sibl(-1), freq(0), anct(_anc), itmset(0), item(_itm) {}

    Arc() = default;
};

extern vector<Arc> Tree;

} // namespace btminer

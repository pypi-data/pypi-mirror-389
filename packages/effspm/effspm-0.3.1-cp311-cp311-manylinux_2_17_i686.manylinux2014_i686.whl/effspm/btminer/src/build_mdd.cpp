#include <vector>
#include <iostream>
#include <unordered_map>
#include <cstdlib>
#include <cmath>

#include "load_inst.hpp"   // ← has: extern unsigned long long E;
#include "build_mdd.hpp"
#include "freq_miner.hpp"
#include "utility.hpp"

namespace btminer {

using std::vector;
using std::unordered_map;
using std::abs;

static int Add_arc(int item,
                   int last_arc,
                   int& itmset,
                   unordered_map<int, int>& ancest_map);

vector<Arc> Tree;   // professor had this global

void Build_MDD(vector<int>& items) {
    unordered_map<int, int> ancest_map;

    int last_arc = 0;
    int itmset   = 0;

    for (int item : items) {
        ++E;   // ✅ count this entry, just like prefix-projection does
        last_arc = Add_arc(item, last_arc, itmset, ancest_map);
    }
}

static int Add_arc(int item,
                   int last_arc,
                   int& itmset,
                   unordered_map<int, int>& ancest_map) {

    int anct;
    auto p = ancest_map.find(std::abs(item));
    if (p == ancest_map.end())
        anct = 0;
    else
        anct = p->second;

    if (item < 0)
        ++itmset;

    int last_sibl = Tree[last_arc].chld;

    if (last_sibl == -1) {
        // create child
        Tree.emplace_back(item, itmset, anct);
        last_sibl = static_cast<int>(Tree.size()) - 1;
        Tree[last_arc].chld = last_sibl;

        if (anct == 0)
            DFS[std::abs(item) - 1].str_pnt.push_back(last_sibl);

    } else {
        // walk siblings
        while (Tree[last_sibl].item != item) {
            if (Tree[last_sibl].sibl == -1) {
                Tree.emplace_back(item, itmset, anct);
                Tree[last_sibl].sibl = static_cast<int>(Tree.size()) - 1;
                last_sibl            = static_cast<int>(Tree.size()) - 1;
                if (anct == 0)
                    DFS[std::abs(item) - 1].str_pnt.push_back(last_sibl);
                break;
            }
            last_sibl = Tree[last_sibl].sibl;
        }
    }

    if (anct == 0)
        ++DFS[std::abs(item) - 1].freq;

    ++Tree[last_sibl].freq;

    ancest_map[std::abs(item)] = last_sibl;

    return last_sibl;
}

} // namespace btminer

#include <unordered_map>
#include <cstdlib>
#include "build_mdd.hpp"
#include "freq_miner.hpp"
#include "load_inst.hpp"

namespace largebm {

std::vector<Arc> Tree;

static int Add_arc(int item,
                   unsigned long long last_arc,
                   int& itmset,
                   std::unordered_map<int, unsigned long long>& ancest_map);

void Build_MDD(const std::vector<int>& items) {
    std::unordered_map<int, unsigned long long> ancest_map;
    unsigned long long last_arc = 0;
    int itmset = 0;
    for (int v : items) {
        last_arc = Add_arc(v, last_arc, itmset, ancest_map);
    }
}

static int Add_arc(int item,
                   unsigned long long last_arc,
                   int& itmset,
                   std::unordered_map<int, unsigned long long>& ancest_map) {
    ++E;

    unsigned idx = static_cast<unsigned>(std::abs(item) - 1);

    if (idx >= DFS.size()) {
        DFS.reserve(idx + 1);
        while (DFS.size() <= idx) {
            DFS.emplace_back(-static_cast<int>(DFS.size()) - 1);
        }
    }

    unsigned long long anct = 0;
    {
        std::unordered_map<int, unsigned long long>::const_iterator p =
            ancest_map.find(std::abs(item));
        if (p != ancest_map.end()) anct = p->second;
    }

    if (item < 0) {
        ++itmset;
    }

    unsigned long long last_sibl = 0;
    if (last_arc < Tree.size()) {
        last_sibl = Tree[last_arc].chld;
    }

    if (last_sibl == 0) {
        Tree.emplace_back(item, itmset, anct);
        last_sibl = Tree.size() - 1;
        if (last_arc < Tree.size()) {
            Tree[last_arc].chld = last_sibl;
        }
        if (anct == 0) {
            DFS[std::abs(item) - 1].str_pnt.push_back(last_sibl);
        }
    } else {
        while (true) {
            if (last_sibl >= Tree.size()) break;
            if (Tree[last_sibl].item == item) {
                break;
            }
            if (Tree[last_sibl].sibl == 0) {
                Tree.emplace_back(item, itmset, anct);
                Tree[last_sibl].sibl = Tree.size() - 1;
                last_sibl = Tree.size() - 1;
                if (anct == 0) {
                    DFS[std::abs(item) - 1].str_pnt.push_back(last_sibl);
                }
                break;
            }
            last_sibl = Tree[last_sibl].sibl;
        }
    }

    if (anct == 0) {
        DFS[std::abs(item) - 1].freq++;
    }

    if (last_sibl < Tree.size()) {
        Tree[last_sibl].freq++;
    }

    ancest_map[std::abs(item)] = last_sibl;
    return static_cast<int>(last_sibl);
}

} // namespace largebm

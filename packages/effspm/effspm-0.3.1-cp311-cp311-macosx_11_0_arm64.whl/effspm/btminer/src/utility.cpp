#include "utility.hpp"
#include "build_mdd.hpp"
#include "load_inst.hpp"
#include <iostream>

namespace btminer {

int find_ID(vector<int>& vec, int itm) {
    int plc = 0;
    while (plc < static_cast<int>(vec.size()) && vec[plc] != itm)
        ++plc;

    if (plc == static_cast<int>(vec.size()))
        return -1;
    else
        return plc;
}

bool check_parent(int cur_arc, int str_pnt, int start, std::vector<int>& strpnt_vec) {

    std::vector<int> ancestors;

    int cur_anct = Tree[cur_arc].anct;

    while (Tree[cur_anct].itmset > Tree[str_pnt].itmset) {
        if (Tree[cur_anct].item > 0)
            ancestors.push_back(cur_anct);
        cur_anct = Tree[cur_anct].anct;
    }

    if (Tree[cur_anct].itmset == Tree[str_pnt].itmset)
        return true;
    else {
        for (auto it = ancestors.rbegin(); it != ancestors.rend(); ++it) {
            for (int i = start; i < static_cast<int>(strpnt_vec.size()); ++i) {
                if (strpnt_vec[i] == *it)
                    return true;
            }
        }
    }

    return false;
}

float give_time(clock_t kk) {
    float ll = static_cast<float>(kk) / CLOCKS_PER_SEC;
    return ll;
}

} // namespace btminer

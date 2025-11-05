#include "utility.hpp"
#include "build_mdd.hpp"
#include "load_inst.hpp"
#include <iostream>

namespace htminer {

using std::vector;

vector<vector<int>> collectedPatterns;

bool check_parent(unsigned int cur_anct, unsigned int str_pnt,
                  unsigned int start, vector<unsigned int>& strpnt_vec) {

    vector<unsigned int> ancestors;

    while (std::abs(Tree[cur_anct].itmset) >
           std::abs(Tree[str_pnt].itmset)) {
        if (Tree[cur_anct].item > 0)
            ancestors.push_back(cur_anct);
        cur_anct = Tree[cur_anct].anct;
    }

    if (std::abs(Tree[cur_anct].itmset) ==
        std::abs(Tree[str_pnt].itmset))
        return true;
    else {
        for (vector<unsigned int>::reverse_iterator it = ancestors.rbegin();
             it != ancestors.rend(); ++it) {
            for (unsigned int i = start; i < strpnt_vec.size(); ++i) {
                if (strpnt_vec[i] == *it)
                    return true;
            }
        }
    }

    return false;
}

float give_time(clock_t kk) {
    float ll = ((float)kk) / CLOCKS_PER_SEC;
    return ll;
}

void ClearCollected() {
    collectedPatterns.clear();
}

const vector<vector<int>>& GetCollected() {
    return collectedPatterns;
}

} // namespace htminer

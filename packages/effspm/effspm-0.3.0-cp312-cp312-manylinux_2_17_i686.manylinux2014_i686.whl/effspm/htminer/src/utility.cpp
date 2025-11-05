#include "utility.hpp"
#include "load_inst.hpp"
#include "freq_miner.hpp"
#include <vector>
namespace htminer {

// ─── Flag‐like globals ──────────────────────────────────────────────────────
bool use_list   = false;
bool just_build = false;
bool b_disp     = false;
bool b_write    = false;
bool use_dic    = false;
bool pre_pro    = false;

unsigned int time_limit = 0;
std::string out_file    = "";
std::clock_t start_time = 0;

// ─── Dataset‐level globals ─────────────────────────────────────────────────
std::vector<std::vector<int>> items;
unsigned long long N     = 0;
unsigned long long L     = 0;
unsigned long long theta = 0;
unsigned int M           = 0;
unsigned long long E     = 0;
unsigned int mlim        = 0; 
// ─── DFS stacks ─────────────────────────────────────────────────────────────
std::vector<Pattern> DFS;
std::vector<VPattern> VDFS;

// ─── Collected patterns storage ────────────────────────────────────────────
std::vector<std::vector<int>> collectedPatterns;
const std::vector<std::vector<int>>& GetCollected() {
    return collectedPatterns;
}

// ─── give_time and check_parent get their definitions here (as provided) ───
float give_time(std::clock_t kk) {
    return static_cast<float>(kk) / static_cast<float>(CLOCKS_PER_SEC);
}
bool check_parent(unsigned int cur_anct, unsigned int str_pnt, unsigned int start, vector<unsigned int>& strpnt_vec) {

	vector<unsigned int> ancestors;
	
	while (abs(Tree[cur_anct].itmset) > abs(Tree[str_pnt].itmset)) {
		if (Tree[cur_anct].item > 0)
			ancestors.push_back(cur_anct);
		cur_anct = Tree[cur_anct].anct;
	}

	if (abs(Tree[cur_anct].itmset) == abs(Tree[str_pnt].itmset))
		return 1;
	else {
		for (vector<unsigned int>::reverse_iterator it = ancestors.rbegin(); it != ancestors.rend(); ++it) {
			for (unsigned int i = start; i < strpnt_vec.size(); ++i) {
				if (strpnt_vec[i] == *it)
					return 1;
			}
		}
	}


	return 0;

}






}
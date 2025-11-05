#include "utility.hpp"
#include <string>

namespace largepp {

// ─── instantiate the globals declared in the header ─────────────
bool  b_disp   = false;
bool  b_write  = false;
bool  use_dic  = false;
bool  just_build = false;
bool  ovr_count  = false;
bool  pre_pro  = false;
bool  use_list = true;          // large-prefix flag the binder toggles
unsigned int time_limit = 36000;
std::string out_file;  
std::vector<std::vector<int>> collected;  // mined pattern output


std::clock_t start_time = 0;

// ─── helper implementations ─────────────────────────────────────
void ClearCollected()                       { collected.clear(); }

const std::vector<std::vector<int>>& GetCollected()
{
    return collected;
}

double give_time(std::clock_t ticks)
{
    return static_cast<double>(ticks) / CLOCKS_PER_SEC;
}

} // namespace largepp

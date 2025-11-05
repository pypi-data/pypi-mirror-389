#include <ctime>       // std::clock
#include <cmath>       // std::ceil, std::abs
#include <algorithm>   // std::max
#include <iostream>    // optional echo
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "load_inst.hpp"
#include "freq_miner.hpp"
#include "utility.hpp"

namespace py = pybind11;

PYBIND11_MODULE(_core, m) {
    m.doc() = "Efficient Sequential Pattern Mining via Prefix-Projection";

    m.def("PrefixProjection",
        [](py::object data,
           double minsup,
           unsigned int time_limit_arg,
           bool preproc_arg,
           bool use_dic_arg,
           bool verbose_arg,
           const std::string &out_file_arg)
        {
            // 1) configure C++ globals
            time_limit = time_limit_arg;
            pre_pro    = preproc_arg;
            use_dic    = use_dic_arg;
            use_list   = false;
            b_disp     = verbose_arg;
            b_write    = !out_file_arg.empty();
            out_file   = out_file_arg;

            // 2) clear collector & start timer
            ClearCollected();
            start_time = std::clock();

            // 3) load either file or in‐memory sequences
            if (py::isinstance<py::str>(data)) {
                auto path = data.cast<std::string>();
                if (!Load_instance(path, minsup))
                    throw std::runtime_error("Failed to load database from " + path);
            }
            else {
                // convert Python List[List[int]] → C++ items
                auto seqs = data.cast<std::vector<std::vector<int>>>();
                items     = std::move(seqs);
                N         = items.size();

                // a) compute max item ID → L
                int max_id = 0;
                for (auto &seq : items)
                    for (int x : seq)
                        max_id = std::max(max_id, std::abs(x));
                L = static_cast<unsigned int>(max_id);

                // b) support threshold θ
                if (minsup < 1.0)
                    theta = static_cast<unsigned long long>(std::ceil(minsup * N));
                else
                    theta = static_cast<unsigned long long>(minsup);

                // c) initialize DFS stack
                DFS.clear();
                DFS.reserve(L);
                for (unsigned int i = 0; i < L; ++i)
                    DFS.emplace_back(-static_cast<int>(i) - 1);

                // d) gather dataset stats: max length M, total entries E
                M = 0;
                E = 0;
                for (auto &seq : items) {
                    M = std::max<unsigned int>(M, static_cast<unsigned int>(seq.size()));
                    E += seq.size();
                }

                if (b_disp) {
                    std::cout << "\nIn-memory dataset: "
                              << N << " sequences, max len " << M
                              << ", " << E << " entries, " << L << " items\n";
                }
            }

            // 4) run the C++ miner
            Freq_miner();

            // 5) collect patterns & timing
            auto patterns   = GetCollected();
            double wall_time = give_time(std::clock() - start_time);

            // 6) return Python dict
            py::dict out;
            out["patterns"] = patterns;
            out["time"]     = wall_time;
            return out;
        },
        py::arg("data"),
        py::arg("minsup")      = 0.01,
        py::arg("time_limit")  = 10 * 3600,
        py::arg("preproc")     = false,
        py::arg("use_dic")     = false,
        py::arg("verbose")     = false,
        py::arg("out_file")    = ""
    );
}

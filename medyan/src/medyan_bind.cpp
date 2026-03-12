/**
 * medyan_bind.cpp
 * ---------------
 * pybind11 bindings for MEDYAN 5.4.0.
 *
 * Exposed Python API
 * ------------------
 *   medyan._core.run_simulation(input_file, input_dir, output_dir,
 *                               runtime=None, seed=None, num_threads=-1)
 *       -> dict  {"filament_coords": [...], "num_filaments": int,
 *                 "num_cylinders": int}
 *
 *   medyan._core.SimulationConfig  – lightweight struct for programmatic access
 *   medyan._core.__version__       – "5.4.0"
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include <filesystem>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

// ---------- MEDYAN headers ----------
// Prevent CATCH2 from hijacking main
#define CATCH_CONFIG_RUNNER
#include "catch2/catch.hpp"

#include "common.h"
#include "MedyanArgs.hpp"
#include "MedyanConfig.hpp"
#include "MedyanMeta.hpp"
#include "Controller/Controller.h"
#include "Structure/Bead.h"
#include "Structure/Cylinder.h"
#include "Structure/Filament.h"

namespace py = pybind11;
using namespace medyan;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/// Snapshot of the current system state, returned to Python as a dict.
struct SystemSnapshot {
    /// Flat list of bead coordinates, one filament per inner vector.
    /// snapshot.filament_coords[i][j] = {x, y, z} of bead j in filament i.
    std::vector<std::vector<std::array<double, 3>>> filament_coords;
    int num_filaments  = 0;
    int num_cylinders  = 0;
    int num_beads      = 0;
};

/// Collect bead coordinates from MEDYAN's static databases right after run().
static SystemSnapshot collectSnapshot() {
    SystemSnapshot snap;

    const auto& filaments = Filament::getFilaments();
    snap.num_filaments = static_cast<int>(filaments.size());

    for (auto* fil : filaments) {
        std::vector<std::array<double, 3>> beadCoords;
        for (auto* cyl : fil->getCylinders()) {
            ++snap.num_cylinders;
            // Each cylinder has a "plus" bead; the last cylinder also has a
            // "minus" bead for the filament tail.
            auto* bead = cyl->getFirstBead();
            if (bead) {
                const auto& c = bead->coordinate();
                beadCoords.push_back({
                    static_cast<double>(c[0]),
                    static_cast<double>(c[1]),
                    static_cast<double>(c[2])
                });
                ++snap.num_beads;
            }
        }
        // Last bead (minus end)
        if (!fil->getCylinders().empty()) {
            auto* lastCyl = fil->getCylinders().back();
            auto* lastBead = lastCyl->getSecondBead();
            if (lastBead) {
                const auto& c = lastBead->coordinate();
                beadCoords.push_back({
                    static_cast<double>(c[0]),
                    static_cast<double>(c[1]),
                    static_cast<double>(c[2])
                });
                ++snap.num_beads;
            }
        }
        snap.filament_coords.push_back(std::move(beadCoords));
    }

    return snap;
}

// ---------------------------------------------------------------------------
// Main entry point exposed to Python
// ---------------------------------------------------------------------------

/**
 * run_simulation(input_file, input_dir, output_dir,
 *                runtime=None, seed=None, num_threads=-1)
 *
 * Mirrors what the MEDYAN binary does when called as:
 *   medyan -s <input_file> -i <input_dir> -o <output_dir>
 *
 * Returns a dict with keys:
 *   "num_filaments"    : int
 *   "num_cylinders"    : int
 *   "num_beads"        : int
 *   "filament_coords"  : list[list[list[float]]]   (filament → bead → [x,y,z])
 */
static py::dict run_simulation(
    const std::string& input_file,
    const std::string& input_dir,
    const std::string& output_dir,
    py::object         runtime_obj,    // float | None
    py::object         seed_obj,       // int   | None
    int                num_threads
) {
    CommandLineConfig cmdConfig;
    cmdConfig.runMode        = MedyanRunMode::simulation;
    cmdConfig.inputFile      = input_file;
    cmdConfig.inputDirectory = input_dir.empty()
                                 ? std::filesystem::path(input_file).parent_path()
                                 : std::filesystem::path(input_dir);
    cmdConfig.outputDirectory = output_dir.empty()
                                  ? std::filesystem::current_path()
                                  : std::filesystem::path(output_dir);
    cmdConfig.numThreads     = num_threads;
    cmdConfig.guiEnabled     = false;

    if (!seed_obj.is_none()) {
        cmdConfig.rngSeedFixed = true;
        cmdConfig.rngSeed = seed_obj.cast<unsigned long long>();
    }

    // Make sure output directory exists.
    std::filesystem::create_directories(cmdConfig.outputDirectory);

    Controller c;
    SimulConfig conf = c.initialize(cmdConfig);

    // Override runtime if provided by the caller.
    if (!runtime_obj.is_none()) {
        conf.geoParams.runTime = runtime_obj.cast<double>();
    }

    c.run(cmdConfig, conf);

    SystemSnapshot snap = collectSnapshot();

    // Convert to Python-friendly types.
    py::list filList;
    for (const auto& filBeads : snap.filament_coords) {
        py::list beadList;
        for (const auto& b : filBeads) {
            beadList.append(py::make_tuple(b[0], b[1], b[2]));
        }
        filList.append(beadList);
    }

    py::dict result;
    result["num_filaments"]   = snap.num_filaments;
    result["num_cylinders"]   = snap.num_cylinders;
    result["num_beads"]       = snap.num_beads;
    result["filament_coords"] = filList;
    return result;
}

// ---------------------------------------------------------------------------
// Module definition
// ---------------------------------------------------------------------------

PYBIND11_MODULE(_core, m) {
    m.doc() = "MEDYAN 5.4.0 Python bindings";
    m.attr("__version__") = "5.4.0";

    m.def(
        "run_simulation",
        &run_simulation,
        py::arg("input_file"),
        py::arg("input_dir")   = std::string(""),
        py::arg("output_dir")  = std::string(""),
        py::arg("runtime")     = py::none(),
        py::arg("seed")        = py::none(),
        py::arg("num_threads") = -1,
        R"pbdoc(
Run a MEDYAN simulation.

Parameters
----------
input_file : str
    Path to the system input file (e.g. systeminput.txt).
input_dir : str, optional
    Directory containing input files (default: directory of input_file).
output_dir : str, optional
    Directory for output files (default: current working directory).
runtime : float, optional
    Override the RUNTIME parameter in the input file.
seed : int, optional
    Fix the RNG seed for reproducibility.
num_threads : int, optional
    Number of threads (-1 = auto).

Returns
-------
dict with keys:
    "num_filaments"   : int
    "num_cylinders"   : int
    "num_beads"       : int
    "filament_coords" : list[list[tuple[float,float,float]]]
        filament_coords[i][j] = (x, y, z) of bead j in filament i
)pbdoc"
    );
}

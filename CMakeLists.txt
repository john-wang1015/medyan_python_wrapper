cmake_minimum_required(VERSION 3.15...4.2)
cmake_policy(SET CMP0169 OLD)  # allow FetchContent_Populate for header-only libs

# Git metadata
macro(git_query _args _var _default)
    execute_process(
        COMMAND git ${_args}
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        OUTPUT_VARIABLE   ${_var}
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET RESULT_VARIABLE _r)
    if(NOT _r EQUAL 0)
        set(${_var} "${_default}")
    endif()
endmacro()
git_query("rev-parse --abbrev-ref HEAD" GIT_BRANCH      "unknown")
git_query("rev-parse HEAD"              GIT_COMMIT_HASH "unknown")
git_query("describe --abbrev=0 --tags"  GIT_LATEST_TAG  "5.4.0")

project(medyan_python VERSION 5.4.0 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)
set(FETCHCONTENT_QUIET OFF)

# ── HDF5 (only true system dependency) ───────────────────────────────────────
find_package(HDF5 REQUIRED COMPONENTS C HL)
message(STATUS "[medyan] HDF5 found: ${HDF5_INCLUDE_DIRS}")

# ── pybind11 ─────────────────────────────────────────────────────────────────
find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
    FetchContent_Declare(pybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
        GIT_TAG        v2.13.6
        GIT_SHALLOW    TRUE)
    FetchContent_MakeAvailable(pybind11)
endif()

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)

# ── Eigen3 (header-only) ─────────────────────────────────────────────────────
find_package(Eigen3 3.4 CONFIG QUIET)
if(NOT Eigen3_FOUND)
    FetchContent_Declare(eigen3
        GIT_REPOSITORY https://gitlab.com/libeigen/eigen.git
        GIT_TAG        3.4.0
        GIT_SHALLOW    TRUE)
    FetchContent_MakeAvailable(eigen3)
    # eigen3's CMakeLists creates Eigen3::Eigen itself — nothing more needed
endif()

# ── fmt ───────────────────────────────────────────────────────────────────────
find_package(fmt CONFIG QUIET)
if(NOT fmt_FOUND)
    FetchContent_Declare(fmt
        GIT_REPOSITORY https://github.com/fmtlib/fmt.git
        GIT_TAG        10.2.1
        GIT_SHALLOW    TRUE)
    FetchContent_MakeAvailable(fmt)
endif()

# ── spdlog ───────────────────────────────────────────────────────────────────
find_package(spdlog CONFIG QUIET)
if(NOT spdlog_FOUND)
    FetchContent_Declare(spdlog
        GIT_REPOSITORY https://github.com/gabime/spdlog.git
        GIT_TAG        v1.14.1
        GIT_SHALLOW    TRUE)
    set(SPDLOG_FMT_EXTERNAL ON CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(spdlog)
endif()

# ── Boost headers ─────────────────────────────────────────────────────────────
find_package(Boost 1.74 QUIET)
if(NOT Boost_FOUND)
    message(STATUS "[medyan] Downloading Boost 1.84.0 headers...")
    FetchContent_Declare(boost_headers
        URL      https://archives.boost.io/release/1.84.0/source/boost_1_84_0.tar.bz2
        URL_HASH SHA256=cc4b893acf645c9d4b698e9a0f08ca8846aa5d6c68275c14c3e7949c24109454)
    FetchContent_MakeAvailable(boost_headers)
    add_library(Boost::boost INTERFACE IMPORTED GLOBAL)
    target_include_directories(Boost::boost INTERFACE "${boost_headers_SOURCE_DIR}")
endif()

# ── Spectra (header-only, needs Eigen3) ──────────────────────────────────────
FetchContent_Declare(spectra
    GIT_REPOSITORY https://github.com/yixuan/spectra.git
    GIT_TAG        v1.0.1
    GIT_SHALLOW    TRUE)
FetchContent_MakeAvailable(spectra)
# spectra's CMakeLists creates Spectra::Spectra

# ── xtl (header-only, required by xtensor) ────────────────────────────────────
FetchContent_Declare(xtl
    GIT_REPOSITORY https://github.com/xtensor-stack/xtl.git
    GIT_TAG        0.7.7
    GIT_SHALLOW    TRUE)
FetchContent_MakeAvailable(xtl)
# xtl's CMakeLists creates xtl target

# ── xtensor (header-only) ─────────────────────────────────────────────────────
FetchContent_Declare(xtensor_fetch
    GIT_REPOSITORY https://github.com/xtensor-stack/xtensor.git
    GIT_TAG        0.25.0
    GIT_SHALLOW    TRUE)
FetchContent_MakeAvailable(xtensor_fetch)
# xtensor's CMakeLists creates xtensor target

# ── HighFive (header-only HDF5 C++ wrapper) ───────────────────────────────────
FetchContent_Declare(HighFive
    GIT_REPOSITORY https://github.com/BlueBrain/HighFive.git
    GIT_TAG        v2.9.0
    GIT_SHALLOW    TRUE)
set(HIGHFIVE_USE_BOOST          OFF CACHE BOOL "" FORCE)
set(HIGHFIVE_USE_EIGEN          OFF CACHE BOOL "" FORCE)
set(HIGHFIVE_USE_XTENSOR        OFF CACHE BOOL "" FORCE)
set(HIGHFIVE_BUILD_DOCS         OFF CACHE BOOL "" FORCE)
set(HIGHFIVE_EXAMPLES           OFF CACHE BOOL "" FORCE)
set(HIGHFIVE_UNIT_TESTS         OFF CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(HighFive)
# HighFive's CMakeLists creates HighFive target
# Aliases expected by MEDYAN's include paths
if(NOT TARGET libdeps)
    add_library(libdeps          INTERFACE IMPORTED GLOBAL)
endif()
if(NOT TARGET HighFive_libdeps)
    add_library(HighFive_libdeps INTERFACE IMPORTED GLOBAL)
endif()
if(NOT TARGET HighFive_HighFive)
    add_library(HighFive_HighFive INTERFACE IMPORTED GLOBAL)
    target_link_libraries(HighFive_HighFive INTERFACE HighFive)
endif()

# ── MEDYAN source files ───────────────────────────────────────────────────────
set(MEDYAN_SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/medyan_src/src")
set(MEDYAN_EXT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/medyan_src/external")

file(GLOB_RECURSE MEDYAN_SRCS
    LIST_DIRECTORIES false CONFIGURE_DEPENDS "${MEDYAN_SRC_DIR}/*.cpp")
list(FILTER MEDYAN_SRCS EXCLUDE REGEX ".*/MEDYAN\\.cpp$")
list(FILTER MEDYAN_SRCS EXCLUDE REGEX ".*\\.cu$")
list(FILTER MEDYAN_SRCS EXCLUDE REGEX ".*CUDAcommon.*")
list(FILTER MEDYAN_SRCS EXCLUDE REGEX ".*/TESTS/.*")
list(FILTER MEDYAN_SRCS EXCLUDE REGEX ".*/Visual/.*")
list(FILTER MEDYAN_SRCS EXCLUDE REGEX ".*VisualSystemRawData.*")

pybind11_add_module(_core MODULE
    ${MEDYAN_SRCS}
    "${CMAKE_CURRENT_SOURCE_DIR}/medyan/src/medyan_bind.cpp"
)

if(MSVC)
    target_compile_options(_core PRIVATE /arch:AVX2 /MP /EHsc /bigobj /W1)
else()
    target_compile_options(_core PRIVATE
        -Wno-sign-compare -Wno-unused-variable -Wno-reorder
        -Wno-unused-but-set-variable -Wno-unused-local-typedefs
        -Wall -ffast-math -fno-finite-math-only -O2 -funroll-loops)
endif()

target_include_directories(_core PRIVATE
    ${MEDYAN_SRC_DIR}
    ${MEDYAN_SRC_DIR}/Chemistry
    ${MEDYAN_SRC_DIR}/Mechanics
    ${MEDYAN_SRC_DIR}/Mechanics/ForceField
    ${MEDYAN_SRC_DIR}/Mechanics/ForceField/Boundary
    ${MEDYAN_SRC_DIR}/Mechanics/ForceField/Branching
    ${MEDYAN_SRC_DIR}/Mechanics/ForceField/Bubble
    ${MEDYAN_SRC_DIR}/Mechanics/ForceField/Filament
    ${MEDYAN_SRC_DIR}/Mechanics/ForceField/Linker
    ${MEDYAN_SRC_DIR}/Mechanics/ForceField/MotorGhost
    ${MEDYAN_SRC_DIR}/Mechanics/ForceField/Volume
    ${MEDYAN_SRC_DIR}/Mechanics/Minimizer
    ${MEDYAN_SRC_DIR}/Structure
    ${MEDYAN_SRC_DIR}/Structure/Special
    ${MEDYAN_EXT_DIR}
)

target_compile_definitions(_core PRIVATE
    GIT_COMMIT_HASH="${GIT_COMMIT_HASH}"
    GIT_BRANCH="${GIT_BRANCH}"
    GIT_LATEST_TAG="${GIT_LATEST_TAG}"
    TRACK_DEPENDENTS TRACK_ZERO_COPY_N TRACK_UPPER_COPY_N
    MOVEBEADSLINESEARCH SIMDBINDINGSEARCH
    BOOST_MEM_POOL BOOL_POOL_NSIZE=65536
    CHECKFORCES_INF_NAN NO_GUI
)
if(MSVC)
    target_compile_definitions(_core PRIVATE _USE_MATH_DEFINES)
endif()

target_link_libraries(_core PRIVATE
    Eigen3::Eigen
    Boost::boost
    fmt::fmt
    spdlog::spdlog
    Spectra::Spectra
    xtensor
    HighFive_HighFive
)

if(NOT MSVC)
    set(THREADS_PREFER_PTHREAD_FLAG ON)
    find_package(Threads REQUIRED)
    target_link_libraries(_core PRIVATE Threads::Threads)
    if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
        target_link_libraries(_core PRIVATE stdc++fs)
    endif()
endif()

install(TARGETS _core DESTINATION medyan)

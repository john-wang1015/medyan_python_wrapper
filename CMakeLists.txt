cmake_minimum_required(VERSION 3.15)

# ── Prevent git-describe from failing inside a non-git checkout ──────────────
execute_process(
    COMMAND           git rev-parse --abbrev-ref HEAD
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    OUTPUT_VARIABLE   GIT_BRANCH
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
    RESULT_VARIABLE   GIT_BRANCH_RESULT
)
if(NOT GIT_BRANCH_RESULT EQUAL 0)
    set(GIT_BRANCH "unknown")
endif()

execute_process(
    COMMAND           git rev-parse HEAD
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    OUTPUT_VARIABLE   GIT_COMMIT_HASH
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
    RESULT_VARIABLE   GIT_HASH_RESULT
)
if(NOT GIT_HASH_RESULT EQUAL 0)
    set(GIT_COMMIT_HASH "unknown")
endif()

execute_process(
    COMMAND           git describe --abbrev=0 --tags
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    OUTPUT_VARIABLE   GIT_LATEST_TAG
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
    RESULT_VARIABLE   GIT_TAG_RESULT
)
if(NOT GIT_TAG_RESULT EQUAL 0)
    set(GIT_LATEST_TAG "5.4.0")
endif()

# vcpkg integration (injected by scikit-build-core via CMAKE_TOOLCHAIN_FILE)
if(DEFINED ENV{VCPKG_DEFAULT_TRIPLET} AND NOT DEFINED VCPKG_TARGET_TRIPLET)
    set(VCPKG_TARGET_TRIPLET "$ENV{VCPKG_DEFAULT_TRIPLET}" CACHE STRING "")
endif()

project(medyan_python VERSION 5.4.0 LANGUAGES CXX)

# ── C++ standard ─────────────────────────────────────────────────────────────
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ── Python / pybind11 ────────────────────────────────────────────────────────
find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

# ── MEDYAN source files ───────────────────────────────────────────────────────
set(MEDYAN_SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/medyan_src/src")
set(MEDYAN_EXT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/medyan_src/external")

# Collect all MEDYAN .cpp files; exclude MEDYAN.cpp (defines main) and CUDA files
file(GLOB_RECURSE MEDYAN_SRCS
    LIST_DIRECTORIES false
    CONFIGURE_DEPENDS
    "${MEDYAN_SRC_DIR}/*.cpp"
)
list(FILTER MEDYAN_SRCS EXCLUDE REGEX ".*/MEDYAN\\.cpp$")
list(FILTER MEDYAN_SRCS EXCLUDE REGEX ".*\\.cu$")
# Remove CUDA-related sources that won't compile without CUDA toolkit
list(FILTER MEDYAN_SRCS EXCLUDE REGEX ".*CUDAcommon.*")

# Binding source
set(BIND_SRC "${CMAKE_CURRENT_SOURCE_DIR}/medyan/src/medyan_bind.cpp")

# ── Build the extension ───────────────────────────────────────────────────────
pybind11_add_module(_core MODULE
    ${MEDYAN_SRCS}
    ${BIND_SRC}
)

# ── Compiler flags ────────────────────────────────────────────────────────────
if(MSVC)
    target_compile_options(_core PRIVATE
        /arch:AVX2 /MP /EHsc /bigobj /W1
    )
else()
    target_compile_options(_core PRIVATE
        -Wno-sign-compare
        -Wno-unused-variable
        -Wno-reorder
        -Wno-unused-but-set-variable
        -Wno-unused-local-typedefs
        -Wall
        -ffast-math
        -fno-finite-math-only
        -O2
        -funroll-loops
    )
endif()

# ── Include paths (mirrors original CMakeLists.txt) ───────────────────────────
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

# ── Preprocessor definitions (matches original) ───────────────────────────────
target_compile_definitions(_core PRIVATE
    GIT_COMMIT_HASH="${GIT_COMMIT_HASH}"
    GIT_BRANCH="${GIT_BRANCH}"
    GIT_LATEST_TAG="${GIT_LATEST_TAG}"

    # Chemistry algorithm
    TRACK_DEPENDENTS
    TRACK_ZERO_COPY_N
    TRACK_UPPER_COPY_N

    # Energy minimization
    MOVEBEADSLINESEARCH

    # Neighbor list
    SIMDBINDINGSEARCH

    # Memory pool
    BOOST_MEM_POOL
    BOOL_POOL_NSIZE=65536

    # Safety checks
    CHECKFORCES_INF_NAN

    # Disable GUI (no OpenGL dependency)
    NO_GUI
)

if(MSVC)
    target_compile_definitions(_core PRIVATE _USE_MATH_DEFINES)
endif()

# ── External dependencies ─────────────────────────────────────────────────────
# These are provided by vcpkg when building via pip / scikit-build-core.

find_package(Boost        REQUIRED COMPONENTS)
find_package(Eigen3       CONFIG   REQUIRED)
find_package(fmt          CONFIG   REQUIRED)
find_package(HighFive     CONFIG   REQUIRED)
find_package(spectra      CONFIG   REQUIRED)
find_package(spdlog       CONFIG   REQUIRED)
find_package(xtensor      CONFIG   REQUIRED)
find_package(Catch2       CONFIG   REQUIRED)

target_link_libraries(_core PRIVATE
    Boost::boost
    Eigen3::Eigen
    fmt::fmt
    libdeps HighFive HighFive_libdeps HighFive_HighFive
    Spectra::Spectra
    spdlog::spdlog spdlog::spdlog_header_only
    xtensor xtensor::optimize
    Catch2::Catch2
)

# Threading
if(NOT MSVC)
    set(THREADS_PREFER_PTHREAD_FLAG ON)
    find_package(Threads REQUIRED)
    target_link_libraries(_core PRIVATE Threads::Threads)

    if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
        target_link_libraries(_core PRIVATE stdc++fs)
    endif()
endif()

# ── Install location (scikit-build-core places it in the Python package dir) ──
install(TARGETS _core DESTINATION medyan)

cmake_minimum_required(VERSION 3.15)

# ─────────────────────────────────────────────────────────────────────────────
# Auto-bootstrap vcpkg
#
# Resolution order (first match wins):
#   1. CMAKE_TOOLCHAIN_FILE already set (user/CI passed it explicitly)
#   2. VCPKG_ROOT environment variable points to an existing vcpkg checkout
#   3. Auto-download vcpkg into <build_dir>/_vcpkg and bootstrap it
#
# This means `pip install git+https://...` works with no extra setup.
# ─────────────────────────────────────────────────────────────────────────────
if(NOT DEFINED CMAKE_TOOLCHAIN_FILE)
    if(DEFINED ENV{VCPKG_ROOT} AND EXISTS "$ENV{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake")
        set(CMAKE_TOOLCHAIN_FILE
            "$ENV{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake"
            CACHE STRING "vcpkg toolchain file")
        message(STATUS "[medyan] Using vcpkg from VCPKG_ROOT=$ENV{VCPKG_ROOT}")
    else()
        set(_VCPKG_AUTO_DIR "${CMAKE_BINARY_DIR}/_vcpkg")

        if(NOT EXISTS "${_VCPKG_AUTO_DIR}/bootstrap-vcpkg.sh" AND
           NOT EXISTS "${_VCPKG_AUTO_DIR}/bootstrap-vcpkg.bat")
            message(STATUS "[medyan] Cloning vcpkg into ${_VCPKG_AUTO_DIR} ...")
            find_package(Git REQUIRED)
            execute_process(
                COMMAND ${GIT_EXECUTABLE} clone
                    --depth 1
                    --branch 2024.04.26
                    https://github.com/microsoft/vcpkg.git
                    "${_VCPKG_AUTO_DIR}"
                RESULT_VARIABLE _VCPKG_CLONE_RESULT
            )
            if(NOT _VCPKG_CLONE_RESULT EQUAL 0)
                message(FATAL_ERROR
                    "[medyan] Failed to clone vcpkg. "
                    "Set VCPKG_ROOT to an existing vcpkg checkout and retry.")
            endif()
        endif()

        if(NOT EXISTS "${_VCPKG_AUTO_DIR}/vcpkg" AND
           NOT EXISTS "${_VCPKG_AUTO_DIR}/vcpkg.exe")
            message(STATUS "[medyan] Bootstrapping vcpkg ...")
            if(WIN32)
                execute_process(
                    COMMAND cmd /c "${_VCPKG_AUTO_DIR}\\bootstrap-vcpkg.bat" -disableMetrics
                    WORKING_DIRECTORY "${_VCPKG_AUTO_DIR}"
                    RESULT_VARIABLE _VCPKG_BOOTSTRAP_RESULT
                )
            else()
                execute_process(
                    COMMAND bash "${_VCPKG_AUTO_DIR}/bootstrap-vcpkg.sh" -disableMetrics
                    WORKING_DIRECTORY "${_VCPKG_AUTO_DIR}"
                    RESULT_VARIABLE _VCPKG_BOOTSTRAP_RESULT
                )
            endif()
            if(NOT _VCPKG_BOOTSTRAP_RESULT EQUAL 0)
                message(FATAL_ERROR "[medyan] vcpkg bootstrap failed.")
            endif()
        endif()

        set(CMAKE_TOOLCHAIN_FILE
            "${_VCPKG_AUTO_DIR}/scripts/buildsystems/vcpkg.cmake"
            CACHE STRING "vcpkg toolchain file (auto-bootstrapped)")
        message(STATUS "[medyan] vcpkg auto-bootstrapped at ${_VCPKG_AUTO_DIR}")
    endif()
endif()

# ── Git metadata (graceful fallback for non-git checkouts) ────────────────────
macro(git_query _CMD _VAR _DEFAULT)
    execute_process(
        COMMAND git ${_CMD}
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        OUTPUT_VARIABLE   ${_VAR}
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
        RESULT_VARIABLE   _GIT_RES
    )
    if(NOT _GIT_RES EQUAL 0)
        set(${_VAR} "${_DEFAULT}")
    endif()
endmacro()
git_query("rev-parse --abbrev-ref HEAD" GIT_BRANCH       "unknown")
git_query("rev-parse HEAD"              GIT_COMMIT_HASH  "unknown")
git_query("describe --abbrev=0 --tags"  GIT_LATEST_TAG   "5.4.0")

if(DEFINED ENV{VCPKG_DEFAULT_TRIPLET} AND NOT DEFINED VCPKG_TARGET_TRIPLET)
    set(VCPKG_TARGET_TRIPLET "$ENV{VCPKG_DEFAULT_TRIPLET}" CACHE STRING "")
endif()

project(medyan_python VERSION 5.4.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ── Python / pybind11 ────────────────────────────────────────────────────────
find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

# ── MEDYAN source files ───────────────────────────────────────────────────────
set(MEDYAN_SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/medyan_src/src")
set(MEDYAN_EXT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/medyan_src/external")

file(GLOB_RECURSE MEDYAN_SRCS
    LIST_DIRECTORIES false CONFIGURE_DEPENDS "${MEDYAN_SRC_DIR}/*.cpp")
list(FILTER MEDYAN_SRCS EXCLUDE REGEX ".*/MEDYAN\\.cpp$")
list(FILTER MEDYAN_SRCS EXCLUDE REGEX ".*\\.cu$")
list(FILTER MEDYAN_SRCS EXCLUDE REGEX ".*CUDAcommon.*")

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

find_package(Boost    REQUIRED COMPONENTS)
find_package(Eigen3   CONFIG REQUIRED)
find_package(fmt      CONFIG REQUIRED)
find_package(HighFive CONFIG REQUIRED)
find_package(spectra  CONFIG REQUIRED)
find_package(spdlog   CONFIG REQUIRED)
find_package(xtensor  CONFIG REQUIRED)
find_package(Catch2   CONFIG REQUIRED)

target_link_libraries(_core PRIVATE
    Boost::boost Eigen3::Eigen fmt::fmt
    libdeps HighFive HighFive_libdeps HighFive_HighFive
    Spectra::Spectra
    spdlog::spdlog spdlog::spdlog_header_only
    xtensor xtensor::optimize
    Catch2::Catch2
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

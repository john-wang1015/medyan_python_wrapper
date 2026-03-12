cmake_minimum_required(VERSION 3.15...4.2)

# ─────────────────────────────────────────────────────────────────────────────
# Auto-bootstrap vcpkg
#
# CMAKE_TOOLCHAIN_FILE MUST be set before project() — we do that here.
#
# Resolution order:
#   1. CMAKE_TOOLCHAIN_FILE already in cache/env  → use as-is
#   2. VCPKG_ROOT env var points to existing vcpkg → use its toolchain
#   3. Auto-clone + bootstrap vcpkg into <build>/_vcpkg
# ─────────────────────────────────────────────────────────────────────────────
if(NOT DEFINED CMAKE_TOOLCHAIN_FILE)
    if(DEFINED ENV{VCPKG_ROOT} AND
       EXISTS "$ENV{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake")
        set(CMAKE_TOOLCHAIN_FILE
            "$ENV{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake"
            CACHE STRING "vcpkg toolchain")
        message(STATUS "[medyan] vcpkg from VCPKG_ROOT=$ENV{VCPKG_ROOT}")
    else()
        set(_VCPKG_DIR "${CMAKE_BINARY_DIR}/_vcpkg")

        # Clone if not already present
        if(NOT EXISTS "${_VCPKG_DIR}/bootstrap-vcpkg.sh" AND
           NOT EXISTS "${_VCPKG_DIR}/bootstrap-vcpkg.bat")
            message(STATUS "[medyan] Cloning vcpkg into ${_VCPKG_DIR} ...")
            find_package(Git REQUIRED)
            # Pin to a known-good commit that does NOT require pkg-config on macOS.
            # This is the same commit MEDYAN's own build system uses.
            set(_VCPKG_COMMIT "c9e786d81a890ef6b3932779925f11e696dc9541")
            execute_process(
                COMMAND ${GIT_EXECUTABLE} clone
                    https://github.com/microsoft/vcpkg.git
                    "${_VCPKG_DIR}"
                RESULT_VARIABLE _CLONE_RES
            )
            if(NOT _CLONE_RES EQUAL 0)
                message(FATAL_ERROR
                    "[medyan] vcpkg clone failed. "
                    "Set VCPKG_ROOT to an existing vcpkg and retry.")
            endif()
            execute_process(
                COMMAND ${GIT_EXECUTABLE} checkout ${_VCPKG_COMMIT}
                WORKING_DIRECTORY "${_VCPKG_DIR}"
                RESULT_VARIABLE _CHECKOUT_RES
            )
            if(NOT _CHECKOUT_RES EQUAL 0)
                message(FATAL_ERROR "[medyan] vcpkg checkout to pinned commit failed.")
            endif()
        endif()

        # Bootstrap (compile the vcpkg binary) if not already done
        if(NOT EXISTS "${_VCPKG_DIR}/vcpkg" AND
           NOT EXISTS "${_VCPKG_DIR}/vcpkg.exe")
            message(STATUS "[medyan] Bootstrapping vcpkg ...")
            if(WIN32)
                execute_process(
                    COMMAND cmd /c "${_VCPKG_DIR}\\bootstrap-vcpkg.bat" -disableMetrics
                    WORKING_DIRECTORY "${_VCPKG_DIR}"
                    RESULT_VARIABLE _BOOT_RES
                )
            else()
                execute_process(
                    COMMAND bash "${_VCPKG_DIR}/bootstrap-vcpkg.sh" -disableMetrics
                    WORKING_DIRECTORY "${_VCPKG_DIR}"
                    RESULT_VARIABLE _BOOT_RES
                )
            endif()
            if(NOT _BOOT_RES EQUAL 0)
                message(FATAL_ERROR "[medyan] vcpkg bootstrap failed.")
            endif()
        endif()

        set(CMAKE_TOOLCHAIN_FILE
            "${_VCPKG_DIR}/scripts/buildsystems/vcpkg.cmake"
            CACHE STRING "vcpkg toolchain (auto-bootstrapped)")
        message(STATUS "[medyan] vcpkg ready at ${_VCPKG_DIR}")
    endif()
endif()

# ── Git metadata (graceful fallback for pip-based checkouts) ──────────────────
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

if(DEFINED ENV{VCPKG_DEFAULT_TRIPLET} AND NOT DEFINED VCPKG_TARGET_TRIPLET)
    set(VCPKG_TARGET_TRIPLET "$ENV{VCPKG_DEFAULT_TRIPLET}" CACHE STRING "")
endif()

# ── Project ───────────────────────────────────────────────────────────────────
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
list(FILTER MEDYAN_SRCS EXCLUDE REGEX ".*/TESTS/.*")

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

# ── External dependencies (installed by vcpkg via vcpkg.json) ─────────────────
find_package(Boost    REQUIRED COMPONENTS)
find_package(Eigen3   CONFIG REQUIRED)
find_package(fmt      CONFIG REQUIRED)
find_package(HighFive CONFIG REQUIRED)
find_package(spectra  CONFIG REQUIRED)
find_package(spdlog   CONFIG REQUIRED)
find_package(xtensor  CONFIG REQUIRED)

target_link_libraries(_core PRIVATE
    Boost::boost Eigen3::Eigen fmt::fmt
    libdeps HighFive HighFive_libdeps HighFive_HighFive
    Spectra::Spectra
    spdlog::spdlog spdlog::spdlog_header_only
    xtensor xtensor::optimize
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

cmake_minimum_required(VERSION 3.15)

#######################################
# Auto-detect conda environment
# Must be done BEFORE project()
#######################################
if(DEFINED ENV{CONDA_PREFIX})
    message(STATUS "Conda environment detected: $ENV{CONDA_PREFIX}")
    list(PREPEND CMAKE_PREFIX_PATH "$ENV{CONDA_PREFIX}")
    include_directories("$ENV{CONDA_PREFIX}/include")
    link_directories("$ENV{CONDA_PREFIX}/lib")
endif()

project(medyan VERSION 5.4.0)

#######################################
# Source files
#######################################

set(src_dir          "src")
set(src_dir_external "external")

file(GLOB_RECURSE src_list LIST_DIRECTORIES true CONFIGURE_DEPENDS "${src_dir}/*.cpp")

#######################################
# Compiling configs
#######################################

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

if(MSVC)
    set(CMAKE_CXX_FLAGS "/arch:AVX2 /MP /EHsc /bigobj")
else()
    set(CMAKE_CXX_FLAGS "-Wno-sign-compare -Wno-unused-variable -Wno-reorder -Wno-unused-but-set-variable -Wno-unused-local-typedefs -Wall -ffast-math -fno-finite-math-only")
    set(CMAKE_CXX_FLAGS_DEBUG "-g")
    set(CMAKE_CXX_FLAGS_RELEASE "-O2 -funroll-loops")
endif()

add_executable(medyan ${src_list})

source_group(TREE ${CMAKE_CURRENT_SOURCE_DIR} FILES ${src_list})

target_include_directories(medyan PUBLIC
    ${src_dir}
    ${src_dir}/Chemistry
    ${src_dir}/Mechanics
    ${src_dir}/Mechanics/ForceField
    ${src_dir}/Mechanics/ForceField/Boundary
    ${src_dir}/Mechanics/ForceField/Branching
    ${src_dir}/Mechanics/ForceField/Bubble
    ${src_dir}/Mechanics/ForceField/Filament
    ${src_dir}/Mechanics/ForceField/Linker
    ${src_dir}/Mechanics/ForceField/MotorGhost
    ${src_dir}/Mechanics/ForceField/Volume
    ${src_dir}/Mechanics/Minimizer
    ${src_dir}/Structure
    ${src_dir}/Structure/Special
    ${src_dir_external}
)

target_compile_definitions(medyan PRIVATE
    GIT_COMMIT_HASH="5.4.0-release"
    GIT_BRANCH="main"
    GIT_LATEST_TAG="v5.4.0"

    TRACK_DEPENDENTS
    TRACK_ZERO_COPY_N
    TRACK_UPPER_COPY_N

    MOVEBEADSLINESEARCH
    SIMDBINDINGSEARCH

    BOOST_MEM_POOL
    BOOL_POOL_NSIZE=65536

    CHECKFORCES_INF_NAN
    NO_GUI
)

if(MSVC)
    target_compile_definitions(medyan PRIVATE _USE_MATH_DEFINES)
endif()

# Threads
if(NOT MSVC)
    set(THREADS_PREFER_PTHREAD_FLAG ON)
    find_package(Threads REQUIRED)
    target_link_libraries(medyan PRIVATE Threads::Threads)
    if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
        target_link_libraries(medyan PRIVATE stdc++fs)
    endif()
endif()

#######################################
# External dependencies
#######################################

# Boost
find_package(Boost CONFIG QUIET)
if(NOT Boost_FOUND)
    cmake_policy(SET CMP0167 OLD)
    find_package(Boost REQUIRED)
endif()
target_link_libraries(medyan PRIVATE Boost::boost)

# Catch2
find_package(Catch2 CONFIG REQUIRED)
target_link_libraries(medyan PRIVATE Catch2::Catch2)

# Eigen3
find_package(Eigen3 CONFIG REQUIRED)
target_link_libraries(medyan PRIVATE Eigen3::Eigen)

# fmt
find_package(fmt CONFIG REQUIRED)
target_link_libraries(medyan PRIVATE fmt::fmt)

# HighFive
find_package(HighFive CONFIG REQUIRED)
if(TARGET HighFive::HighFive)
    target_link_libraries(medyan PRIVATE HighFive::HighFive)
elseif(TARGET HighFive)
    target_link_libraries(medyan PRIVATE HighFive)
else()
    message(FATAL_ERROR "HighFive found but no known CMake target available.")
endif()

# Spectra — header-only, no CMake config file on conda-forge.
# Headers are already available via include_directories($CONDA_PREFIX/include) above.
# No find_package needed.

# spdlog
find_package(spdlog CONFIG REQUIRED)
target_link_libraries(medyan PRIVATE spdlog::spdlog spdlog::spdlog_header_only)

# xtensor
find_package(xtensor CONFIG REQUIRED)
target_link_libraries(medyan PRIVATE xtensor xtensor::optimize)

#######################################
# Install
#######################################

install(TARGETS medyan
    RUNTIME DESTINATION medyan/bin
)

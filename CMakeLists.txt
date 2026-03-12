cmake_minimum_required(VERSION 3.15)

#######################################
# Configurations
#######################################

project(medyan VERSION 5.4.0)

#######################################
# Source files
#######################################

set(src_dir          "src")
set(src_dir_external "external")

# List sources
file(GLOB_RECURSE src_list LIST_DIRECTORIES true CONFIGURE_DEPENDS "${src_dir}/*.cpp")

#######################################
# Compiling configs
#######################################

# C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Compiler flags
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

# Add the executable
add_executable(medyan ${src_list})

# Source groups for IDEs
source_group(TREE ${CMAKE_CURRENT_SOURCE_DIR} FILES ${src_list})

# Include paths
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

# Preprocessor macros
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

    # Always disable GUI for the Python package build
    NO_GUI
)

if(MSVC)
    target_compile_definitions(medyan PRIVATE
        _USE_MATH_DEFINES
    )
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

# boost
find_package(Boost REQUIRED COMPONENTS)
target_link_libraries(medyan PRIVATE Boost::boost)

# catch2
find_package(Catch2 CONFIG REQUIRED)
target_link_libraries(medyan PRIVATE Catch2::Catch2)

# eigen3
find_package(Eigen3 CONFIG REQUIRED)
target_link_libraries(medyan PRIVATE Eigen3::Eigen)

# fmt
find_package(fmt CONFIG REQUIRED)
target_link_libraries(medyan PRIVATE fmt::fmt)

# highfive (HDF5 C++ wrapper)
# conda-forge provides the target HighFive::HighFive; vcpkg uses libdeps + HighFive.
find_package(HighFive CONFIG REQUIRED)
if(TARGET HighFive::HighFive)
    target_link_libraries(medyan PRIVATE HighFive::HighFive)
elseif(TARGET HighFive)
    # vcpkg-style targets
    target_link_libraries(medyan PRIVATE libdeps HighFive HighFive_libdeps HighFive_HighFive)
else()
    message(FATAL_ERROR "HighFive found but no known CMake target available.")
endif()

# spectra
find_package(spectra CONFIG REQUIRED)
target_link_libraries(medyan PRIVATE Spectra::Spectra)

# spdlog
find_package(spdlog CONFIG REQUIRED)
target_link_libraries(medyan PRIVATE spdlog::spdlog spdlog::spdlog_header_only)

# xtensor
find_package(xtensor CONFIG REQUIRED)
target_link_libraries(medyan PRIVATE xtensor xtensor::optimize)

#######################################
# Install rules (used by scikit-build-core)
#######################################

# Install the medyan executable into the Python package's bin/ directory.
# scikit-build-core will place it relative to the package root.
install(TARGETS medyan
    RUNTIME DESTINATION medyan/bin
)

add_executable(flow5_run flow5_run.cpp)
target_compile_features(flow5_run PRIVATE cxx_std_20)
target_include_directories(flow5_run PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(flow5_run PRIVATE flow5-lib)
set_target_properties(flow5_run PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/run
    BUILD_RPATH "${CMAKE_BINARY_DIR}/flow5-lib;${CMAKE_BINARY_DIR}/XFoil-lib;${CMAKE_BINARY_DIR}/gmsh-staging/usr/lib/x86_64-linux-gnu;/usr/lib/x86_64-linux-gnu;/usr/local/lib"
    INSTALL_RPATH "${CMAKE_BINARY_DIR}/flow5-lib;${CMAKE_BINARY_DIR}/XFoil-lib;${CMAKE_BINARY_DIR}/gmsh-staging/usr/lib/x86_64-linux-gnu;/usr/lib/x86_64-linux-gnu;/usr/local/lib"
)

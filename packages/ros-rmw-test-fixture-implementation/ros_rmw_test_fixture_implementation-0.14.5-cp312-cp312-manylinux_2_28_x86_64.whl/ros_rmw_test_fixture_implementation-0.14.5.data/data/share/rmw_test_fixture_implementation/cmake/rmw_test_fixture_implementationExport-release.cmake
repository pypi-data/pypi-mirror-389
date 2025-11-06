#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rmw_test_fixture_implementation::rmw_test_fixture_implementation" for configuration "Release"
set_property(TARGET rmw_test_fixture_implementation::rmw_test_fixture_implementation APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rmw_test_fixture_implementation::rmw_test_fixture_implementation PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_RELEASE "rcpputils::rcpputils;rcutils::rcutils;rmw::rmw"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/librmw_test_fixture_implementation.so"
  IMPORTED_SONAME_RELEASE "librmw_test_fixture_implementation.so"
  )

list(APPEND _cmake_import_check_targets rmw_test_fixture_implementation::rmw_test_fixture_implementation )
list(APPEND _cmake_import_check_files_for_rmw_test_fixture_implementation::rmw_test_fixture_implementation "${_IMPORT_PREFIX}/lib/librmw_test_fixture_implementation.so" )

# Import target "rmw_test_fixture_implementation::run_rmw_isolated" for configuration "Release"
set_property(TARGET rmw_test_fixture_implementation::run_rmw_isolated APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rmw_test_fixture_implementation::run_rmw_isolated PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/rmw_test_fixture_implementation/run_rmw_isolated"
  )

list(APPEND _cmake_import_check_targets rmw_test_fixture_implementation::run_rmw_isolated )
list(APPEND _cmake_import_check_files_for_rmw_test_fixture_implementation::run_rmw_isolated "${_IMPORT_PREFIX}/lib/rmw_test_fixture_implementation/run_rmw_isolated" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)

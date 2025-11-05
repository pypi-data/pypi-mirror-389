#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rosidl_dynamic_typesupport_fastrtps::rosidl_dynamic_typesupport_fastrtps" for configuration "Release"
set_property(TARGET rosidl_dynamic_typesupport_fastrtps::rosidl_dynamic_typesupport_fastrtps APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rosidl_dynamic_typesupport_fastrtps::rosidl_dynamic_typesupport_fastrtps PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/librosidl_dynamic_typesupport_fastrtps.so"
  IMPORTED_SONAME_RELEASE "librosidl_dynamic_typesupport_fastrtps.so"
  )

list(APPEND _cmake_import_check_targets rosidl_dynamic_typesupport_fastrtps::rosidl_dynamic_typesupport_fastrtps )
list(APPEND _cmake_import_check_files_for_rosidl_dynamic_typesupport_fastrtps::rosidl_dynamic_typesupport_fastrtps "${_IMPORT_PREFIX}/lib/librosidl_dynamic_typesupport_fastrtps.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)

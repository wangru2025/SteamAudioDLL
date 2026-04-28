cmake_minimum_required(VERSION 3.20)
project(SteamAudioDLL CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(STEAMAUDIO_AUTO_DOWNLOAD "Automatically download the Steam Audio SDK when it is not available locally." ON)
set(STEAMAUDIO_VERSION "4.8.0" CACHE STRING "Steam Audio SDK version to use when auto-downloading.")
set(STEAMAUDIO_ARCHIVE_SHA512 "fa77d71de2080f3c5d75fbbc1345f1894abef9df7c2a1373331cb190ca214c8f48be7e7cda1f495aeab258395669cf8eddea8e1cab19ff43607cc2945a679b38" CACHE STRING "Expected SHA512 for the downloaded Steam Audio archive.")
set(STEAMAUDIO_SDK_PATH "" CACHE PATH "Path to an existing Steam Audio SDK root. Leave empty to use the repository copy or auto-download.")

function(resolve_steam_audio_sdk out_root)
    set(candidate_roots)

    if(STEAMAUDIO_SDK_PATH)
        list(APPEND candidate_roots "${STEAMAUDIO_SDK_PATH}")
    endif()

    list(APPEND candidate_roots
        "${CMAKE_CURRENT_SOURCE_DIR}/steamaudio"
        "${CMAKE_CURRENT_BINARY_DIR}/_deps/steamaudio/steamaudio"
    )

    foreach(candidate IN LISTS candidate_roots)
        set(candidate_valid FALSE)

        if(WIN32)
            if(
                EXISTS "${candidate}/include/phonon.h"
                AND EXISTS "${candidate}/lib/windows-x64/phonon.lib"
                AND EXISTS "${candidate}/lib/windows-x64/phonon.dll"
            )
                set(candidate_valid TRUE)
            endif()
        elseif(APPLE)
            if(
                EXISTS "${candidate}/include/phonon.h"
                AND EXISTS "${candidate}/lib/osx/libphonon.dylib"
            )
                set(candidate_valid TRUE)
            endif()
        elseif(UNIX)
            if(
                EXISTS "${candidate}/include/phonon.h"
                AND EXISTS "${candidate}/lib/linux-x64/libphonon.so"
            )
                set(candidate_valid TRUE)
            endif()
        endif()

        if(candidate_valid)
            cmake_path(ABSOLUTE_PATH candidate NORMALIZE OUTPUT_VARIABLE candidate_abs)
            set(${out_root} "${candidate_abs}" PARENT_SCOPE)
            return()
        endif()
    endforeach()

    if(NOT STEAMAUDIO_AUTO_DOWNLOAD)
        message(FATAL_ERROR "Steam Audio SDK not found. Set STEAMAUDIO_SDK_PATH or enable STEAMAUDIO_AUTO_DOWNLOAD.")
    endif()

    set(download_dir "${CMAKE_CURRENT_BINARY_DIR}/_deps/downloads")
    set(extract_dir "${CMAKE_CURRENT_BINARY_DIR}/_deps/steamaudio")
    set(archive_path "${download_dir}/steamaudio_${STEAMAUDIO_VERSION}.zip")
    set(extracted_root "${extract_dir}/steamaudio")

    file(MAKE_DIRECTORY "${download_dir}")
    file(MAKE_DIRECTORY "${extract_dir}")

    if(NOT EXISTS "${archive_path}")
        message(STATUS "Downloading Steam Audio SDK v${STEAMAUDIO_VERSION}")
        file(
            DOWNLOAD
            "https://github.com/ValveSoftware/steam-audio/releases/download/v${STEAMAUDIO_VERSION}/steamaudio_${STEAMAUDIO_VERSION}.zip"
            "${archive_path}"
            EXPECTED_HASH "SHA512=${STEAMAUDIO_ARCHIVE_SHA512}"
            SHOW_PROGRESS
            TLS_VERIFY ON
        )
    endif()

    if(NOT EXISTS "${extracted_root}/include/phonon.h")
        message(STATUS "Extracting Steam Audio SDK to ${extract_dir}")
        file(ARCHIVE_EXTRACT INPUT "${archive_path}" DESTINATION "${extract_dir}")
    endif()

    if(
        NOT EXISTS "${extracted_root}/include/phonon.h"
        OR NOT EXISTS "${extracted_root}/lib/windows-x64/phonon.lib"
        OR NOT EXISTS "${extracted_root}/lib/windows-x64/phonon.dll"
    )
        message(FATAL_ERROR "Steam Audio SDK extraction failed or is incomplete under ${extracted_root}.")
    endif()

    cmake_path(ABSOLUTE_PATH extracted_root NORMALIZE OUTPUT_VARIABLE extracted_root_abs)
    set(${out_root} "${extracted_root_abs}" PARENT_SCOPE)
endfunction()

resolve_steam_audio_sdk(STEAMAUDIO_SDK_ROOT)

set(STEAMAUDIO_INCLUDE_DIR "${STEAMAUDIO_SDK_ROOT}/include")

if(WIN32)
    set(STEAMAUDIO_LIB_DIR "${STEAMAUDIO_SDK_ROOT}/lib/windows-x64")
    set(STEAMAUDIO_RUNTIME_DLLS
        "${STEAMAUDIO_LIB_DIR}/phonon.dll"
        "${STEAMAUDIO_LIB_DIR}/GPUUtilities.dll"
        "${STEAMAUDIO_LIB_DIR}/TrueAudioNext.dll"
    )
elseif(APPLE)
    set(STEAMAUDIO_LIB_DIR "${STEAMAUDIO_SDK_ROOT}/lib/osx")
elseif(UNIX)
    set(STEAMAUDIO_LIB_DIR "${STEAMAUDIO_SDK_ROOT}/lib/linux-x64")
endif()

if(MINGW)
    if(EXISTS "${STEAMAUDIO_LIB_DIR}/libphonon.a")
        set(PHONON_LIB "${STEAMAUDIO_LIB_DIR}/libphonon.a")
    else()
        message(FATAL_ERROR "libphonon.a not found at ${STEAMAUDIO_LIB_DIR}.")
    endif()
else()
    find_library(PHONON_LIB
        NAMES phonon
        PATHS "${STEAMAUDIO_LIB_DIR}"
        NO_DEFAULT_PATH
    )
    if(NOT PHONON_LIB)
        message(FATAL_ERROR "Steam Audio library not found at ${STEAMAUDIO_LIB_DIR}")
    endif()
endif()

message(STATUS "Using Steam Audio SDK: ${STEAMAUDIO_SDK_ROOT}")
message(STATUS "Using Steam Audio library: ${PHONON_LIB}")

# Source files
set(SOURCES
    src/phonon_wrapper.cpp
    src/audio_processor.cpp
    src/audio_mixer.cpp
    src/geometry_scene.cpp
    src/direct_simulator.cpp
    src/room_reverb.cpp
    src/direct_effect.cpp
    src/c_interface.cpp
)

set(HEADERS
    include/phonon_wrapper.h
    include/audio_processor.h
    include/audio_mixer.h
    include/geometry_scene.h
    include/direct_simulator.h
    include/room_reverb.h
    include/direct_effect.h
    include/c_interface.h
)

# Create DLL
add_library(SteamAudioDLL SHARED ${SOURCES} ${HEADERS})

# Add export definition
target_compile_definitions(SteamAudioDLL PRIVATE STEAMAUDIO_BUILDING_DLL)

# Include directories
target_include_directories(SteamAudioDLL PRIVATE
    "${STEAMAUDIO_INCLUDE_DIR}"
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
)

# Link libraries
target_link_libraries(SteamAudioDLL PRIVATE
    "${PHONON_LIB}"
)

# Static link all MinGW runtime libraries for complete portability
if(MINGW)
    # Link static runtime libraries
    target_link_options(SteamAudioDLL PRIVATE -static-libgcc -static-libstdc++)
    
    # Also link pthread statically
    target_link_libraries(SteamAudioDLL PRIVATE -static)
endif()

# Set output directory
set_target_properties(SteamAudioDLL PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

if(WIN32)
    list(GET STEAMAUDIO_RUNTIME_DLLS 0 STEAMAUDIO_PHONON_DLL)
    list(GET STEAMAUDIO_RUNTIME_DLLS 1 STEAMAUDIO_GPUUTILITIES_DLL)
    list(GET STEAMAUDIO_RUNTIME_DLLS 2 STEAMAUDIO_TRUEAUDIONEXT_DLL)

    add_custom_command(TARGET SteamAudioDLL POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E make_directory
            "${CMAKE_CURRENT_SOURCE_DIR}/python-steamaudio/steamaudio/bindings/dll"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "$<TARGET_FILE:SteamAudioDLL>"
            "${CMAKE_CURRENT_SOURCE_DIR}/python-steamaudio/steamaudio/bindings/dll/SteamAudioDLL.dll"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "${STEAMAUDIO_PHONON_DLL}"
            "$<TARGET_FILE_DIR:SteamAudioDLL>/phonon.dll"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "${STEAMAUDIO_GPUUTILITIES_DLL}"
            "$<TARGET_FILE_DIR:SteamAudioDLL>/GPUUtilities.dll"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "${STEAMAUDIO_TRUEAUDIONEXT_DLL}"
            "$<TARGET_FILE_DIR:SteamAudioDLL>/TrueAudioNext.dll"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "${STEAMAUDIO_PHONON_DLL}"
            "${CMAKE_CURRENT_SOURCE_DIR}/python-steamaudio/steamaudio/bindings/dll/phonon.dll"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "${STEAMAUDIO_GPUUTILITIES_DLL}"
            "${CMAKE_CURRENT_SOURCE_DIR}/python-steamaudio/steamaudio/bindings/dll/GPUUtilities.dll"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "${STEAMAUDIO_TRUEAUDIONEXT_DLL}"
            "${CMAKE_CURRENT_SOURCE_DIR}/python-steamaudio/steamaudio/bindings/dll/TrueAudioNext.dll"
    )
endif()

# Export symbols for C interface
if(MSVC)
    target_compile_options(SteamAudioDLL PRIVATE /W4)
endif()

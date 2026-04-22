cmake_minimum_required(VERSION 3.20)
project(SteamAudioDLL CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Steam Audio SDK path - adjust this to your installation
set(STEAMAUDIO_SDK_PATH "steamaudio" CACHE PATH "Steam Audio SDK installation path")

# For MinGW, we need to find the .a library file
if(MINGW)
    # First check if libphonon.a exists (generated from DLL)
    if(EXISTS "${STEAMAUDIO_SDK_PATH}/lib/windows-x64/libphonon.a")
        set(PHONON_LIB "${STEAMAUDIO_SDK_PATH}/lib/windows-x64/libphonon.a")
        message(STATUS "Found MinGW library: ${PHONON_LIB}")
    else()
        message(FATAL_ERROR "libphonon.a not found. Please generate it from phonon.dll using dlltool.")
    endif()
else()
    find_library(PHONON_LIB 
        NAMES phonon
        PATHS "${STEAMAUDIO_SDK_PATH}/lib/windows-x64"
        NO_DEFAULT_PATH
    )
    if(NOT PHONON_LIB)
        message(FATAL_ERROR "Steam Audio library not found at ${STEAMAUDIO_SDK_PATH}/lib/windows-x64")
    endif()
endif()

message(STATUS "Using Steam Audio library: ${PHONON_LIB}")

# Source files
set(SOURCES
    src/phonon_wrapper.cpp
    src/audio_processor.cpp
    src/audio_mixer.cpp
    src/room_reverb.cpp
    src/direct_effect.cpp
    src/c_interface.cpp
)

set(HEADERS
    include/phonon_wrapper.h
    include/audio_processor.h
    include/audio_mixer.h
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
    "${STEAMAUDIO_SDK_PATH}/include"
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
    add_custom_command(TARGET SteamAudioDLL POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "${CMAKE_CURRENT_SOURCE_DIR}/${STEAMAUDIO_SDK_PATH}/lib/windows-x64/phonon.dll"
            "$<TARGET_FILE_DIR:SteamAudioDLL>/phonon.dll"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "${CMAKE_CURRENT_SOURCE_DIR}/${STEAMAUDIO_SDK_PATH}/lib/windows-x64/GPUUtilities.dll"
            "$<TARGET_FILE_DIR:SteamAudioDLL>/GPUUtilities.dll"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "${CMAKE_CURRENT_SOURCE_DIR}/${STEAMAUDIO_SDK_PATH}/lib/windows-x64/TrueAudioNext.dll"
            "$<TARGET_FILE_DIR:SteamAudioDLL>/TrueAudioNext.dll"
    )
endif()

# Export symbols for C interface
if(MSVC)
    target_compile_options(SteamAudioDLL PRIVATE /W4)
endif()

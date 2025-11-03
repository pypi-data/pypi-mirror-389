
################################################################################
##                                                                            ##
##  This file is part of MCPL (see https://mctools.github.io/mcpl/)           ##
##                                                                            ##
##  Copyright 2015-2025 MCPL developers.                                      ##
##                                                                            ##
##  Licensed under the Apache License, Version 2.0 (the "License");           ##
##  you may not use this file except in compliance with the License.          ##
##  You may obtain a copy of the License at                                   ##
##                                                                            ##
##      http://www.apache.org/licenses/LICENSE-2.0                            ##
##                                                                            ##
##  Unless required by applicable law or agreed to in writing, software       ##
##  distributed under the License is distributed on an "AS IS" BASIS,         ##
##  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  ##
##  See the License for the specific language governing permissions and       ##
##  limitations under the License.                                            ##
##                                                                            ##
################################################################################

cmake_policy(PUSH)#NB: We POP at the end of this file.
cmake_policy(VERSION 3.16...3.31)

if(TARGET MCPLGeant4::MCPLGeant4)
  return()
endif()

#Export a few directory paths (relocatable):
set( MCPLGeant4_CMAKEDIR "${CMAKE_CURRENT_LIST_DIR}" )
set( MCPLGeant4_INCDIR "${CMAKE_CURRENT_LIST_DIR}/include" )
set( MCPLGeant4_SRCDIR "${CMAKE_CURRENT_LIST_DIR}/src" )
set(
  MCPLGeant4_SRCFILES
  "${MCPLGeant4_SRCDIR}/G4MCPLGenerator.cc"
  "${MCPLGeant4_SRCDIR}/G4MCPLWriter.cc"
)

include( CMakeFindDependencyMacro )

if( NOT TARGET MCPL::MCPL )
  if ( NOT DEFINED MCPL_DIR )
    execute_process(
      COMMAND "mcpl-config" "--show" "cmakedir"
      OUTPUT_VARIABLE MCPL_DIR
      OUTPUT_STRIP_TRAILING_WHITESPACE
    )
  endif()
  find_dependency( MCPL 1.9.80 REQUIRED )
endif()

if ( NOT Geant4_LIBRARIES )
  message(
    FATAL_ERROR
    "Make sure your find_package(Geant4) call comes before find_package(MCPLGeant4)"
  )
endif()

set_source_files_properties(
  ${MCPLGeant4_SRCFILES}
  PROPERTIES LANGUAGE "CXX"
)

add_library( MCPLGeant4 STATIC EXCLUDE_FROM_ALL ${MCPLGeant4_SRCFILES} )
add_library( MCPLGeant4::MCPLGeant4 ALIAS MCPLGeant4 )

target_link_libraries(
  MCPLGeant4
  PUBLIC MCPL::MCPL ${Geant4_LIBRARIES}
)

target_include_directories(
  MCPLGeant4
  PUBLIC "${MCPLGeant4_INCDIR}"
)

cmake_policy(POP)

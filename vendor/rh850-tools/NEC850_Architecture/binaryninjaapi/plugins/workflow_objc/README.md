# Objective-C Workflow

This is the Objective-C plugin that ships with Binary Ninja. It provides
additional support for analyzing Objective-C binaries.

The primary functionality offered by this plugin is:

1. Automatic inlining of the `objc_msgSend$foo:bar:` selector stub functions.
2. Automatic call type adjustments for calls to `objc_msgSend` and `objc_msgSendSuper2`.
   Call types are adjusted at each call site to set the number of arguments that are expected
   based on the selector. Argument names are derived from the selector components, and argument
   types are inferred in limited cases.
3. Direct call rewriting.  Calls to `objc_msgSend` can be rewritten to be direct calls to
   the first known method implementation for that selector. This is disabled by default
   as it will give potentially confusing results for any selector that has more than one
   implementation or for common selector names. That said, some users may still find it to
   be useful. It can be enabled via the `analysis.objectiveC.resolveDynamicDispatch`
   setting.
  
For more details and usage instructions, see the [user guide](https://dev-docs.binary.ninja/guide/objectivec.html).

## Issues

Please file issues at https://github.com/Vector35/binaryninja-api/issues.

## Building

This plugin can be built and installed separately from Binary Ninja via the
following commands:

```sh
git clone https://github.com/Vector35/binaryninja-api.git && cd binaryninja-api
git submodule update --init --recursive
cmake -S plugins/workflow_objc -B build -G Ninja
cmake --build build -t install
```

## Credits

This plugin is a continuation of [Objective Ninja](https://github.com/jonpalmisc/ObjectiveNinja),
originally made by [@jonpalmisc](https://twitter.com/jonpalmisc).

The full terms of the original Objective Ninja license are as follows:

```
Copyright (c) 2022-2023 Jon Palmisciano

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software without
   specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

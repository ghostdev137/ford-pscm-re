{ pkgs ? import <nixpkgs> {} }:
  pkgs.mkShell {
   nativeBuildInputs = with pkgs; [
      cmake
      clang
      darwin.apple_sdk.frameworks.CoreServices
    ];
}
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    
    python3
    python3Packages.pip
    libheif
    libde265      # Hardware/software decoder for HEIF
    libtiff
    openjpeg
    freetype
    libgpiod
    avahi
    openblas
    swig
    libffi        # Essential for Python C-extensions
    chromium
    noto-fonts-color-emoji
    pkg-config
    gcc
    # pip install --force-reinstall --no-binary pi-heif pi-heif
    
  ];

  shellHook = ''
    # Construct the library path cleanly
    export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [ 
      pkgs.libheif pkgs.libde265 pkgs.libtiff pkgs.openjpeg pkgs.freetype pkgs.libgpiod pkgs.openblas pkgs.libffi
    ]}"

    # Add headers for Python compilation
    export CPATH="${pkgs.lib.makeSearchPathOutput "dev" "include" [ 
      pkgs.libheif pkgs.libtiff pkgs.openjpeg pkgs.freetype pkgs.libgpiod
    ]}"
  '';
}
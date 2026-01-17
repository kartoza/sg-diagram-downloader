# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: GPL-2.0
{
  description = "NixOS developer environment for SG Diagram Downloader QGIS plugin.";
  inputs.qgis-upstream.url = "github:qgis/qgis";
  inputs.geospatial.url = "github:imincik/geospatial-nix.repo";
  inputs.nixpkgs.follows = "geospatial/nixpkgs";

  outputs =
    {
      self,
      qgis-upstream,
      geospatial,
      nixpkgs,
    }:
    let
      system = "x86_64-linux";
      profileName = "SGDiagramDownloader";
      pkgs = import nixpkgs {
        inherit system;
        config = {
          allowUnfree = true;
        };
      };

      extraPythonPackages = ps: [
        ps.pyqtwebengine
        ps.debugpy
        ps.psutil
        ps.requests
      ];
      qgisWithExtras = geospatial.packages.${system}.qgis.override {
        inherit extraPythonPackages;
      };
      qgisLtrWithExtras = geospatial.packages.${system}.qgis-ltr.override {
        inherit extraPythonPackages;
      };
      qgisMasterWithExtras = qgis-upstream.packages.${system}.qgis.override {
        inherit extraPythonPackages;
      };
    in
    {
      packages.${system} = {
        default = qgisWithExtras;
        qgis = qgisWithExtras;
        qgis-ltr = qgisLtrWithExtras;
        qgis-master = qgisMasterWithExtras;
      };

      apps.${system} = {
        qgis = {
          type = "app";
          program = "${qgisWithExtras}/bin/qgis";
          args = [
            "--profile"
            "${profileName}"
          ];
        };
        qgis-ltr = {
          type = "app";
          program = "${qgisLtrWithExtras}/bin/qgis";
          args = [
            "--profile"
            "${profileName}"
          ];
        };
        qgis-master = {
          type = "app";
          program = "${qgisMasterWithExtras}/bin/qgis";
          args = [
            "--profile"
            "${profileName}"
          ];
        };
        qgis_process = {
          type = "app";
          program = "${qgisWithExtras}/bin/qgis_process";
          args = [
            "--profile"
            "${profileName}"
          ];
        };
      };

      devShells.${system}.default = pkgs.mkShell {
        packages = [
          qgisWithExtras
          pkgs.actionlint
          pkgs.bandit
          pkgs.chafa
          pkgs.nixfmt-rfc-style
          pkgs.git
          pkgs.glow
          pkgs.gum
          pkgs.isort
          pkgs.jq
          pkgs.markdownlint-cli
          pkgs.pre-commit
          pkgs.shellcheck
          pkgs.shfmt
          pkgs.yamlfmt
          pkgs.yamllint
          pkgs.nodePackages.cspell
          (pkgs.python3.withPackages (ps: [
            ps.black
            ps.click
            ps.debugpy
            ps.docformatter
            ps.flake8
            ps.httpx
            ps.mypy
            ps.pip
            ps.psutil
            ps.pytest
            ps.pytest-qt
            ps.requests
            ps.rich
            ps.setuptools
            ps.toml
            ps.typer
            ps.wheel
            ps.pyqt5-stubs
            ps.venvShellHook
            ps.virtualenv
            ps.pyqtwebengine
          ]))
        ];
        shellHook = ''
          unset SOURCE_DATE_EPOCH

          # Create a virtual environment in .venv if it doesn't exist
          if [ ! -d ".venv" ]; then
            python -m venv .venv
          fi

          # Activate the virtual environment
          source .venv/bin/activate

          # Upgrade pip and install packages from requirements.txt if it exists
          pip install --upgrade pip > /dev/null
          if [ -f requirements.txt ]; then
            echo "Installing Python requirements from requirements.txt..."
            pip install -r requirements.txt > .pip-install.log 2>&1
            if [ $? -ne 0 ]; then
              echo "Pip install failed. See .pip-install.log for details."
            fi
          else
            echo "No requirements.txt found, skipping pip install."
          fi
          if [ -f requirements-dev.txt ]; then
            echo "Installing Python requirements from requirements-dev.txt..."
            pip install -r requirements-dev.txt > .pip-install.log 2>&1
            if [ $? -ne 0 ]; then
              echo "Pip install failed. See .pip-install.log for details."
            fi
          else
            echo "No requirements-dev.txt found, skipping pip install."
          fi

          # Add PyQt and QGIS to python path for neovim
          pythonWithPackages="${
            pkgs.python3.withPackages (ps: [
              ps.pyqt5-stubs
              ps.pyqtwebengine
            ])
          }"
          export PYTHONPATH="$pythonWithPackages/lib/python*/site-packages:${qgisWithExtras}/share/qgis/python:$PYTHONPATH"

          # Colors and styling
          CYAN='\033[38;2;83;161;203m'
          GREEN='\033[92m'
          RED='\033[91m'
          RESET='\033[0m'
          ORANGE='\033[38;2;237;177;72m'
          GRAY='\033[90m'

          # Clear screen and show welcome banner
          clear
          echo -e "$RESET$ORANGE"
          if [ -f "resources/icon.png" ]; then
            chafa resources/icon.png --size=20x40 --colors=256 | sed 's/^/                  /'
          fi

          echo -e "$RESET$ORANGE \n__________________________________________________________________\n"
          echo -e "        SG Diagram Downloader Dev Environment"
          echo -e ""
          echo -e "Quick Commands:$RESET"
          echo -e "   $GRAY>$RESET  $CYAN./scripts/checks.sh$RESET  - Run pre-commit checks"
          echo -e "   $GRAY>$RESET  $CYAN./scripts/clean.sh$RESET   - Cleanup dev folder"
          echo -e "   $GRAY>$RESET  $CYAN nix flake show$RESET      - Show available configurations"
          echo -e "   $GRAY>$RESET  $CYAN nix flake check$RESET     - Run all checks"
          echo -e "$RESET$ORANGE \n__________________________________________________________________\n"
          echo "To run QGIS with your profile, use one of these commands:"
          echo -e "$RESET$ORANGE \n__________________________________________________________________\n"
          echo ""
          echo "  scripts/start_qgis.sh"
          echo "  scripts/start_qgis_ltr.sh"
          echo "  scripts/start_qgis_master.sh"
          echo ""
        '';
      };
    };
}

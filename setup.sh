#!/bin/bash
set -e

# Install build dependencies
sudo pacman -S --needed base-devel python-setuptools

# Build and install the package
makepkg -si --noextract

# Enable and start the systemd user service
systemctl --user enable rewind-screenshot.service
systemctl --user start rewind-screenshot.service

echo "Rewind has been installed successfully!"
echo "You can now use the 'rewind' command to search your screenshots."

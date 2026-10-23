# Dotbot yay Plugin

For use with [dotbot](https://github.com/anishathalye/dotbot),
this plugin installs a list of Arch packages: official repo packages with `pacman`, AUR packages with `yay`.

This plugin is a port of [dotbot-yaourt](https://github.com/niklas-heer/dotbot-yaourt) for use with `yay`. Basically the same thing with a `:%s/yaourt/yay` command ran, plus a couple other relevant changes.

[dotbot-yaourt](https://github.com/niklas-heer/dotbot-yaourt) was itself heavily inspired by the [apt-get](https://github.com/rubenvereecken/dotbot-apt-get) plugin.

## Usage

It's easiest to track this plugin in your dotfiles repo:

```bash
git submodule add https://github.com/oxson/dotbot-yay
```

If you use the default install script provided by [dotbot](https://github.com/anishathalye/dotbot), using the plugin will look like this:

```bash
./dotbot/bin/dotbot -p dotbot-yay/yay.py -c packages.conf.yaml
```

Using the `install` script provided by this repo, using the plugin will look like this:
```bash
./install packages
```

Example for `packages.conf.yaml`:

```yaml
- pacman:      # official repos, installed with `sudo pacman`
  - vim
  - zsh
  - tldr
- yay:         # AUR, built by `yay` as your own user
  - oh-my-posh-bin
  - zen-browser-bin
```

Run dotbot as your normal user. `pacman` asks for your password through `sudo`; `yay` does not need root.

## Changes in this fork

Upstream runs `yay --needed -S <pkg>` once per package, with a one second sleep before each, and works out
what happened by searching yay's output for strings. With a long list that is slow even when everything is
already installed, and it breaks when the output changes or is not UTF-8.

- **Fast skip.** `pacman -Qq` is read once. Installed packages print `Package "x" is already installed.`
  and are not passed to an installer at all. A run with nothing missing takes about a second.
- **One batch.** Everything missing goes to a single `... --needed --noconfirm -S a b c` call.
- **Failure handling.** If the batch fails, the missing packages are retried one at a time, and the ones
  that still fail are listed at the end. The result is the installer's exit code, so output is not parsed.
- **`pacman` directive.** Repo packages and AUR packages can live in separate lists.
- Adds a `.gitignore`.

Groups and "provides" names (`base-devel`, for example) are not in `pacman -Qq`, so they are always
passed to the installer. `--needed` makes that a no-op when they are already satisfied.

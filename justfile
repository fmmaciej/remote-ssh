# shellcheck shell=bash

@_default:
    just --list

lint:
    just -f dev/justfile py-lint
    just -f dev/justfile sh-lint

sync:
    just -f dev/justfile sync

pre-commit-install:
    just -f dev/justfile pre-commit-install

pre-commit:
    just -f dev/justfile pre-commit

fmt:
    just -f dev/justfile py-fmt
    just -f dev/justfile sh-fmt

type:
    just -f dev/justfile py-type

smoke:
    just -f dev/justfile smoke

test: smoke

test-assets-live:
    just -f dev/justfile test-assets-live

all: lint fmt type

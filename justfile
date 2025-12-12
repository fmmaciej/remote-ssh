# shellcheck shell=bash

@_default:
    just --list

lint:
    just -f dev/justfile py-lint
    just -f dev/justfile sh-lint

fmt:
    just -f dev/justfile py-fmt
    just -f dev/justfile sh-fmt

type:
    just -f dev/justfile py-type

all: lint fmt type

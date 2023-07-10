# ![vanilla](https://assets.ubuntu.com/v1/70041419-vanilla-framework.png?w=35 'Vanilla') Vanilla Framework

[![CircleCI build status](https://circleci.com/gh/canonical/vanilla-framework.svg?style=shield)](https://circleci.com/gh/canonical/vanilla-framework)
[![npm version](https://badge.fury.io/js/vanilla-framework.svg)](http://badge.fury.io/js/vanilla-framework)
[![Downloads](http://img.shields.io/npm/dm/vanilla-framework.svg)](https://www.npmjs.com/package/vanilla-framework)
[![devDependency Status](https://david-dm.org/canonical/vanilla-framework/dev-status.svg)](https://david-dm.org/canonical/vanilla-framework#info=devDependencies)
[![Chat in #vanilla-framework on Freenode](https://img.shields.io/badge/chat-%23vanilla--framework-blue.svg)](http://webchat.freenode.net/?channels=vanilla-framework)
[![This project is using Percy.io for visual regression testing.](https://percy.io/static/images/percy-badge.svg)](https://percy.io)

Vanilla Framework is an extensible CSS framework, built using [Sass](http://sass-lang.com/) and is designed to be used either directly or by using themes to extend or supplement its patterns.

[Documentation](https://vanillaframework.io/docs) |
[Join the mailing list](http://canonical.us3.list-manage2.com/subscribe?u=56dac47c206ba0f58ec25f314&id=36f7d8394e)

## Table of contents

- [Using Vanilla](#using-vanilla)
  - [Hotlinking](#hotlinking)
  - [Including Vanilla in your project via NPM](#including-vanilla-in-your-project-via-npm)
- [Developing Vanilla](#developing-vanilla)
- [Community](#community)

## Using Vanilla

### Hotlinking

You can link to the latest build to add directly into your markup like so, by replacing the x values with the [version number you wish to link](https://github.com/canonical/vanilla-framework/releases).

```html
<link rel="stylesheet" href="https://assets.ubuntu.com/v1/vanilla-framework-version-x.x.x.min.css" />
```

### Including Vanilla in your project via NPM or yarn

To get set up with Sass, add the `sass` and `vanilla-framework` packages to your project dependencies:

```bash
yarn add sass vanilla-framework
```

In the script that builds the CSS in your `package.json`, you should include the path to `node_modules` when looking for `@imports`. In this example, we have called the build script `"build-css"`:

```
"build-css": "sass -w --load-path=node_modules src:dist --style=compressed"
```

Make a folder `src/`, create a file inside called `style.scss` and import Vanilla:

```sass
// Import the theme
@import 'vanilla-framework';
@include vanilla;

// Optionally override some settings
$color-brand: #ffffff;

// Add theme if applicable
```

If you don't want the whole framework, you can just `@include` specific [parts](scss) - e.g. `@include vf-b-forms`.

Now run `yarn build-css`, which will convert any Sass files in the `src/` folder to CSS in the `dist/` folder.

To watch for changes in your Sass files, add the following script to your `package.json`

```
"watch-css":  "yarn build-css && sass --load-path=node_modules -w src:dist --style=compressed"
```

## Developing Vanilla

If you're looking to contribute to the Vanilla project itself, [start here](/CONTRIBUTING.md).

- [Code of conduct](/CONTRIBUTING.md#code-of-conduct)
- [Reporting bugs and issues](/CONTRIBUTING.md#reporting-bugs-and-issues)
- [Working with the Vanilla project](/CONTRIBUTING.md#working-with-the-vanilla-project)
- [Pull requests](/CONTRIBUTING.md#pull-requests)
- [Releasing Vanilla](/CONTRIBUTING.md#releasing-vanilla)

## Community

Keep up to date with all new developments and upcoming changes with Vanilla.

- Follow us on Twitter [@vanillaframewrk](https://twitter.com/vanillaframewrk)
- Read our latest blog posts at [Ubuntu Blog](https://blog.ubuntu.com/topics/design)

Code licensed [LGPLv3](http://opensource.org/licenses/lgpl-3.0.html) by [Canonical Ltd](http://www.canonical.com/)

With ♥ from Canonical

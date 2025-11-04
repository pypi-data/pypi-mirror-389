# Template for Rucio policy packages
This repository includes a template policy package that is ready to be customised and used.

## Steps
1. Create a new repository using this template
2. Rename the folder within `src/` to the name of your policy package
3. Update `pyproject.toml` with your information
4. Adapt the permission, schema and algorithms to your needs

## Building and publishing a policy package
This template provides a GitHub Action workflow for building and publishing a policy package to PyPI;
you can trigger this action by publishing a new release on GitHub.

## Pointing to your policy package as a requirement
Once released, you can specify your policy package as a requirement
by either pointing to its published distribution on PyPI
or by pointing to its GitHub release.

### Pointing to the published package
The standard way is to point to the package published on PyPI
in the same way as any other Python dependency:

```
package-name==version
```

For example, a policy package `atlas-rucio-policy-package` could be listed like this:

```
atlas-rucio-policy-package==0.5.0
```

### Pointing to the GitHub release
You can also point directly to the GitHub release, by specifying:

```
package-name @ git+https://github.com/[username]/package-name@tag
```

This way, you can also avoid publishing to PyPI, and you can remove the PyPI publishing step from the GitHub Action.

For example, a `belleii-rucio-policy-package` could be listed like this:

```
belleii-rucio-policy-package @ git+https://github.com/rucio/temporary-belle2-policy-package@v0.1.1
```

## Default algorithms
Rucio supports [default algorithms for policy packages](https://rucio.github.io/documentation/operator/policy_packages/policy-package-algorithms#default-algorithms), to simplify the configuration process.
In this template, the `lfn2pfn` algorithm is defined as a default algorithm.

## Resources
- [Rucio documentation for policy packages](https://rucio.github.io/documentation/operator/policy_packages/policy_packages_overview/)

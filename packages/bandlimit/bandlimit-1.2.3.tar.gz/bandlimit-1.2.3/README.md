# Single Point Gaussian integral in Sinc space
## bandlimit

## <Gaussian | Sinc>

### Conceptual

Gaussians are primitive data types on a lattice, Sincs are the collection of maximumally localized bandlimited planewaves.
Let the two have fun together!

### How to install

`pip install bandlimit`

`from bandlimit.gaussian import compute`

## for a angular_gaussian like (x-y)^n * exp(-0.5 alpha (x-y)**2) 
## compute(lattice, n, alpha, y, X)  = < normalized_angular_gaussian(n) @ y | Sinc @ X in lattice >


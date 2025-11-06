iso639
======
A simple (really simple) library for working with ISO639-3 language codes.
Tested for Python 2.7 & 3.4.

Includes data from Congress library: http://www.loc.gov/standards/iso639-2/php/code_list.php (+ updates)

Installation
------------
The easiest way is using `pip`:

    pip install langiso639

If you are using Fedora 24+, you can install iso639 using dnf:

    dnf install python2-langiso639
    # or
    dnf install python3-langiso639

Thanks, unknown Fedora packagers :-)

Alternatives
------------
* **pycountry**: https://bitbucket.org/flyingcircus/pycountry - a more-featured package
* **iso639**: https://github.com/noumar/iso639 - another package with the same name

Example usage
-------------

```python
import langiso639

>>> langiso639.to_name('sv')
u'Swedish'

>>> langiso639.to_native('sv')
u'svenska'
``

pkgname=rewind
pkgver=0.1
pkgrel=1
pkgdesc="App for creating recurring screenshots with text recognition and the ability to search through the created screenshots."
arch=('any')
url="https://github.com/Forwall100/rewind"
license=('MIT')
depends=('python' 'python-pillow' 'python-pytesseract' 'python-yaml' 'tesseract' 'tesseract-data-eng' 'tesseract-data-rus' 'grim' 'scrot')
makedepends=('python-setuptools')
source=()

package() {
	cd "$startdir"
	python setup.py install --root="$pkgdir" --optimize=1
	install -Dm644 config.yaml "$pkgdir/etc/rewind/config.yaml"
	install -Dm644 rewind-screenshot.service "$pkgdir/usr/lib/systemd/user/rewind-screenshot.service"
	install -Dm755 rewind.sh "$pkgdir/usr/bin/rewind"
}

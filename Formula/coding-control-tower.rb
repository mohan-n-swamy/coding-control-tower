class CodingControlTower < Formula
  include Language::Python::Virtualenv

  desc "Local, project-first dashboard for coding sessions and pull requests"
  homepage "https://github.com/mohan-n-swamy/coding-control-tower"
  url "https://github.com/mohan-n-swamy/coding-control-tower/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "REPLACE_WITH_RELEASE_TARBALL_SHA256"
  license "MIT"

  depends_on "python@3.13"

  def install
    # Stdlib-only package: no resources to vendor.
    virtualenv_install_with_resources
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/coding-control-tower --version")
    assert_match "doctor", shell_output("#{bin}/coding-control-tower --help")
  end
end

class CodingControlTower < Formula
  include Language::Python::Virtualenv

  desc "Local, project-first dashboard for coding sessions and pull requests"
  homepage "https://github.com/mohan-n-swamy/coding-control-tower"
  url "https://github.com/mohan-n-swamy/coding-control-tower/archive/refs/tags/v0.2.0.tar.gz"
  sha256 "a54ad6f96602ee3072dba921dd6cee37d1aaaa73536149a44b29951aa6b90283"
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

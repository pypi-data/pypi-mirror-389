#include <map>
#include <vector>
#include <iostream>

using namespace std;

void psfmult_impl(const vector<double> &psf,
		  const vector<int> &x,
		  const vector<int> &y,
		  const vector<int> &z,

		  vector<double> &out_psfpsf,
		  vector<int> &out_x,
		  vector<int> &out_y,
		  vector<int> &out_z)
{

  struct Diff {
    Diff() {}
    Diff(int x, int y, int z): dx(x), dy(y), dz(z) {}
    
    int dx;
    int dy;
    int dz;
    
    bool operator<(const Diff &b) const {
      return (dx<b.dx) ||
	(dx==b.dx && ( (dy<b.dy) ||
		       (dy==b.dy && (dz<b.dz))));
    }
  };

  map< Diff, double > psfpsf;
  const size_t sz = psf.size();
  for (size_t i=0; i < sz; ++i) {
    for (size_t j=0; j < sz; ++j) {
      Diff d( x[i]-x[j],
	      y[i]-y[j],
	      z[i]-z[j] );
      double v = psf[i]*psf[j];
      auto iter = psfpsf.find(d);
      if (iter == psfpsf.end())
	psfpsf[d] = v;
      else
	iter->second += v;
    }
  }

  const size_t osz = psfpsf.size();
  cout << "PSF*PSF calculated and merged into a map. Found unique combinations: " << osz << endl;
  size_t i = 0;
  out_psfpsf.resize(osz);
  out_x.resize(osz);
  out_y.resize(osz);
  out_z.resize(osz);
  for (auto iter = psfpsf.cbegin(); iter != psfpsf.cend(); ++iter, ++i)
    {
      const Diff &k = iter->first;
      out_x[i] = k.dx;
      out_y[i] = k.dy;
      out_z[i] = k.dz;
      out_psfpsf[i] = iter->second;
    }
}


from GCR import GCRQuery
from .base import BaseValidationTest, TestResult
from .plotting import plt
from .utils import get_opt_binpoints

__all__ = ['SizeDistribution']

class SizeDistribuction(BaseValidationTest):
    """
    validation test to check the slope of the size distribution at small sizes.
    """

    #plotting constants
    validation_color = 'black'
    validation_marker = 'o'
    default_markers = ['v', 's', 'd', 'H', '^', 'D', 'h', '<', '>', '.']
    msize = 4 #marker-size
    yaxis_xoffset = 0.02
    yaxis_yoffset = 0.5

    def __init__(self, observation='', **kwargs):

        #validation data
        validation_filepath = os.path.join(self.data_dir, kwargs['data_filename'])
        self.validation_data = np.loadtxt(validation_filepath)
        
        self.acceptable_keys = kwargs['possible_size_fields']

        #check for valid observations
        if not observation:
            print('Warning: no data file supplied, no observation requested; only catalog data will be shown')
        elif observation not in self.possible_observations:
            raise ValueError('Observation {} not available'.format(observation))
        else:
            self.validation_data = self.get_validation_data(observation)

        self._color_iterator = ('C{}'.format(i) for i in count())
        self._other_kwargs = kwargs        

    def run_on_single_catalog(self, catalog_instance, catalog_name, output_dir):
        # update color and marker to preserve catalog colors and markers across tests
        catalog_color = next(self._color_iterator)

        # check catalog data for required quantities
        key = catalog_instance.first_available(*self.acceptable_keys)
        if not key:
            summary = 'Missing required quantity' + ' or '.join(['{}']*len(self.acceptable_keys)
            return TestResult(skipped=True, summary=summary.format(*self.acceptable_keys))

        # get data
        catalog_data = catalog_instance.get_quantities(key)
        sizes = catalog_data[key]
        min_sizes = np.min(sizes)
        max_sizes = np.max(sizes)
        
        # Compute N(size) and its slope at the small end.
        # Things seem to be roughly linear where N(size)>0.5*Ntot so use those points.
        # Get ~20 points for the line fit, but compute the whole graph
        median = np.median(sizes)
        n_bins = int(20*(max_sizes-min_sizes)/(median-min_sizes)) 
        N, bin_edges = np.histogram(sizes, bins=n_bins)
        sumM = np.histogram(sizes, weights=sizes, bins=bin_edges)[0]
        sumM2 = np.histogram(sizes, weights=sizes**2, bins=bin_edges)[0]
        size_pts = get_opt_binpoints(N, sumM, sumM2, bin_edges)

        mask = size_pts<median

        # Normalize so we can compare datasets of different sizes
        cumul_N_norm = np.array(
                [1.0*np.sum(N[-i-1:]) for i in range(len(N))], dtype=float
            )[::-1]/np.sum(N)
        data_slope, data_intercept = np.polyfit(size_pts[mask], cumul_N_norm[mask], 1)
        
        # Compute the slope for the validation dataset in this size range.
        mask = (validation_data[:,0] > min_sizes) & (validation_data[:,0]<median)
        validation_data[:,1] /= validation_data[mask,1][0]
        validation_slope, validation_intercept = np.polyfit(validation_data[mask, 0],
                                                            validation_data[mask, 1], 1)

        # plot a histogram of sizes. This is easier to see as log(sizes) so do that.
        fig, (hist_ax, cumul_ax) = plt.subplots(1, 2)
        hist_ax.hist(np.log(sizes), color=catalog_color, edgecolor='black', alpha=0.75, 
                     normed=True, bins=log_bin_edges)
        hist_ax.set_xlabel("Log({})".format(key))
        hist_ax.set_ylabel("dN/d log({})".format(key))
        
        # plot the CDF and the line fit
        cumul_ax.plot(size_pts, cumul_N, color=catalog_color)
        cumul_ax.plot(size_pts[mask], (data_intercept+data_slope*size_pts[mask]), color='gray')
        cumul_ax.set_xscale('log')
        cumul_ax.text(0.95, 0.96,
                      'validation slope=${:.3f}$\nslope=${:.3f}$'.format(validation_slope, data_slope), 
                      horizontalalignment='right', verticalalignment='top',
                      transform=cumul_ax.transAxes)
        cumul_ax.set_xlabel("{}".format(key))
        cumul_ax.set_ylabel("N({})".format(key))

        with open(os.path.join(output_dir, 'size_distribution_{}.txt'.format(catalog_name)), 'ab'
                 ) as f:
            f.write("# Slope, intercept\n")
            f.write("%7f  %9f\n"%(data_slope, data_intercept) 

        fig.savefig(os.path.join(output_dir, 'size_distribution_{}.png'.format(catalog_name)))
        plt.close(fig)
        return TestResult(0, passed=True)


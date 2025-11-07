import numpy as np
import os
import uproot
import pickle
from .data import DataLoader, Sample
from .bookkeeping.paths import Paths
from .physics.clustering import Clustering
from .physics.clustering import diagnostics
from .utils.slicing_utils import copy_fields

class Project:
    """
    Base class for all projects
    """
    def __init__(self, name, description, mu, **parameters):
        self.n_events = {'sig': parameters.pop('n_sig_events'), 'bg': parameters.pop('n_bg_events')}
        self.sample_path = parameters.pop('sample_path', Paths.get_sample_path())
        self.cellmap_path = parameters.pop('cellmap_path', Paths.get_cellmap_path())
        self.name = name
        self.parameters = parameters
        self.description = description
        self.mu = mu
        self.bg_data = self.__load("bg") 
        self.sig_data = self.__load("sig")

    def __load(self, sig_or_bg):
        key = f"pickle_{sig_or_bg}"
        if key in self.parameters:
            pickle_path = self.parameters[key]
            if os.path.isfile(pickle_path):
                data = pickle.load(open(pickle_path, "rb"))
            else:
                data = self.get_preprocessed_data(sig_or_bg)
                pickle.dump(data, open(pickle_path, "wb"))
        else:
            data = self.get_preprocessed_data(sig_or_bg)
        return data
 
    def __not_impl_error_msg(self, fname):
        return f"Must implement {fname} in your project class"

    def get_sample_names(self, sig_or_bg):
        raise NotImplementedError(self.__not_impl_error_msg("get_sample_names"))

    def load_raw_data(self, sig_or_bg, n_events, path=Paths.get_sample_path()):
        # TODO support multiple samples
        return [DataLoader(Sample.from_ds_name(path, s, mu=self.mu)).load(n_events=n_events) for s in self.get_sample_names(sig_or_bg)][0]

    def load_raw_cellmap(self, path=Paths.get_cellmap_path()):
        cell_map = uproot.open(path)['caloCellsMap'].arrays()
        return cell_map

    def get_preprocessed_data(self, sig_or_bg):
        raise NotImplementedError(self.__not_impl_error_msg("get_preprocessed_data"))

    def get_baseline_rate(self, data=None):
        if data is None:
            data = self.bg_data
        baseline_trigger = self.get_baseline_trigger()
        return baseline_trigger.counts(data)

    def get_baseline_efficiency(self, truth_data, eta_key, phi_key, dR_window=0.2, bins=np.arange(0, 120000, 2000)):
        baseline_trigger = self.get_baseline_trigger()
        curve = baseline_trigger.efficiency(truth_data, eta_key=eta_key, phi_key=phi_key, dR_cutoff=dR_window, bins=bins)
        return curve

    def get_baseline_trigger(self):
        raise NotImplementedError(self.__not_impl_error_msg("get_baseline_trigger"))

class SeededRectangularClusters(Project):
    """
    Base class for all projects that rely on clustering around seeds.
    A discriminants class instance can be provided, which is used to compute the discriminants
       on the fly as part of the preprocessing of data
    """
    def __init__(self, name, description, mu, **parameters):
        """
        Expects:
           - clus_cfg - instance of the ClusteringConfig class or its derivative
        """
        self.clus_cfg = parameters.pop("clus_cfg")
        self.discriminants = parameters.pop("discriminants", None)
        self.discriminant_params = parameters.pop("discriminant_params", {})
        self.fields_to_keep = parameters.pop("fields_to_keep", None)
        super().__init__(name, description, mu, **parameters)

    def get_discriminant_keys(self):
        assert self.discriminants is not None, "No discriminants set"
        return self.discriminants.get_discriminant_keys()

    def compute_discriminants(self, clusters, keep_clusters):
        if self.discriminants is not None:
            discr = self.discriminants(clusters, self.discriminant_params).compute()
            if keep_clusters:
                return merge_disjoint_fields([clusters, discr])
            return discr
        return clusters

    def get_preprocessed_data(self, sig_or_bg, keep_clusters=False):
        data = self.load_raw_data(sig_or_bg, self.n_events[sig_or_bg], self.sample_path)
        cell_map = self.load_raw_cellmap(self.cellmap_path)

        clusters = Clustering(self.clus_cfg).cluster(data, cell_map)
        diagnostics.plot_cluster_size(clusters)
        diagnostics.assert_cluster_size(clusters, self.clus_cfg.cluster_r_eta, self.clus_cfg.cluster_r_phi)
        diagnostics.plot_cluster_non_zeros(clusters)
        diagnostics.plot_cell_et(clusters)

        if self.fields_to_keep:
            # fields_to_keep is a list of fields to keep
            clusters = copy_fields(clusters, data, self.fields_to_keep)

        return self.compute_discriminants(clusters, keep_clusters)


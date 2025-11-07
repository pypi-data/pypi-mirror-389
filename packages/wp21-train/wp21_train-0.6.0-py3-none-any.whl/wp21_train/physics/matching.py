import awkward as ak
import vector
from ..utils.slicing_utils import add_zero_fields, rename_fields, merge_disjoint_fields

def match_arrays_by_dR(data, dR_cutoff, left_keys, left_phi, left_eta, right_keys, right_phi, right_eta):
    """
    For each object in left, will find a matching object in right within deltaR<dR_cutoff.
      If multiple are found, will return the closest one. If none are found, will have an empty list in the fields with the names
      provided in right_keys

      data - awkward array
      left_keys - all keys we want to keep from left
      left_phi - the label of the phi field
      left_eta - the label of the eta field
      right_keys - all keys we want to keep from right
      right_phi - the label of the phi field
      right_eta - the label of the eta field

      returns - awkward array with all the content of left_keys, and matching objects in right_keys for each object in left keys.
        When no match, an empty list is placed in right_keys for that particular object.
    """
    vector.register_awkward()
    
    left=data[left_keys]
    left = ak.with_name(add_zero_fields(rename_fields(left, {left_phi: "phi", left_eta: "eta"}), ["pt", "mass"]), "Momentum4D")
    right = data[right_keys]
    right = ak.with_name(add_zero_fields(rename_fields(right, {right_phi: "phi", right_eta: "eta"}), ["pt", "mass"]), "Momentum4D")
    
    dR = left[:, :, None].deltaR(right[:, None, :])
    l,r = ak.broadcast_arrays(left, right[:,None,:])
    mask = dR < dR_cutoff
    tmp = ak.with_field(r, dR, "dR")[mask]
    idx_min = ak.argmin(tmp["dR"], axis=2)
    selected = rename_fields(tmp[ak.local_index(tmp["dR"], axis=2) == idx_min], {"phi": right_phi, "eta": right_eta})
   
    to_zip = dict([(f, selected[f]) for f in selected.fields if f not in ["pt", "mass"]]) 
    other = ak.Array(to_zip)
    return merge_disjoint_fields([data[left_keys], other])


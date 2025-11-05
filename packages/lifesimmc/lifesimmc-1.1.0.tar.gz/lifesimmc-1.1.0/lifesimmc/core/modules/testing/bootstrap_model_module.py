import torch

from lifesimmc.core.modules.base_module import BaseModule
from lifesimmc.core.resources.base_resource import BaseResource
from lifesimmc.core.resources.data_resource import DataResource
from lifesimmc.core.resources.test_resource import TestResourceCollection


class BModelModule(BaseModule):
    """Class representation of an energy detector test module.

    :param n_data_in: Name of the input data resource.
    :param n_test_out: Name of the output test resource.
    :param pfa: Probability of false alarm.
    """

    def __init__(
            self,
            n_data_in: str,
            n_config_in: str = None,
            n_data_out: str = None,
            add: bool = True,
    ):
        """Constructor method.

        :param n_data_in: Name of the input data resource.
        :param n_test_out: Name of the output test resource.
        :param pfa: Probability of false alarm.
        :param n_config_in: Name of the input configuration resource.
        :param n_cov_in: Name of the input covariance resource.
        :param n_coordinate_in: Name of the input coordinate resource.
        :param n_flux_in: Name of the input flux resource.
        :param use_theoretical: Whether to calculate the theoretical or empirical test statistic.
        """
        self.n_data_in = n_data_in
        self.n_config_in = n_config_in
        self.n_data_out = n_data_out
        # self.n_cov_in = n_cov_in
        # self.n_coordinate_in = n_coordinate_in
        # self.n_flux_in = n_flux_in
        self.add = add

    def apply(self, resources: list[BaseResource]) -> TestResourceCollection:
        """Apply the energy detector test.

        :param resources: List of resources.
        :return: Test resource collection.
        """
        print("Performing energy detector test...")

        r_data_out = DataResource(self.n_data_out) if self.n_data_out is not None else None

        # Extract all inputs
        r_config_in = self.get_resource_from_name(self.n_config_in) if self.n_config_in is not None else None
        # r_cov_in = self.get_resource_from_name(self.n_cov_in) if self.n_cov_in is not None else None
        # r_coordinate_in = self.get_resource_from_name(
        #     self.n_coordinate_in
        # ) if self.n_coordinate_in is not None else None

        data = self.get_resource_from_name(self.n_data_in).get_data()
        #
        # plt.imshow(data[0])
        # plt.colorbar()
        # plt.show()

        num_of_diff_outputs = len(data)
        time = r_config_in.phringe.get_time_steps(as_numpy=True)
        self.wavelengths = r_config_in.phringe.get_wavelength_bin_centers(as_numpy=True)
        self.wavelength_bin_widths = r_config_in.phringe.get_wavelength_bin_widths(as_numpy=True)
        # i_cov_sqrt = r_cov_in.i_cov_sqrt.cpu().numpy()

        # Generate a purely diagonal covariance matrix if none is given
        # if not self.use_theoretical:
        #     flux_in = r_config_in.scene.planets[0].spectral_flux_density.cpu().numpy()
        #     x_pos = r_config_in.scene.planets[0].angular_separation_from_star_x.cpu().numpy()[0]
        #     y_pos = r_config_in.scene.planets[0].angular_separation_from_star_y.cpu().numpy()[0]
        #
        # else:
        #     i_cov_sqrt = torch.diag(
        #         torch.ones(data.shape[1], device=r_config_in.phringe._director._device)
        #     ).unsqueeze(0).repeat(data.shape[0], 1, 1).cpu().numpy()
        #     x_pos = np.array(r_coordinate_in.x)
        #     y_pos = np.array(r_coordinate_in.y)
        #     # TODO: Handle multiple planets
        #     flux_in = self.get_resource_from_name(self.n_flux_in).collection[0].spectral_irradiance.cpu().numpy() \
        #         if self.n_flux_in is not None else None

        for i in range(num_of_diff_outputs):

            sky_brightness_distribution = r_config_in.phringe._director._planets[
                0].sky_brightness_distribution  # TODO: Handel multiple planets
            # Get indices of only pixel that is not zero
            index_x, index_y = torch.nonzero(sky_brightness_distribution[0], as_tuple=True)
            # index_x, index_y = index_x[0].item(), index_y[0].item()
            x_coord = r_config_in.phringe._director._planets[0].sky_coordinates[
                0, index_x[0].item(), index_y[0].item()].cpu().numpy()
            y_coord = r_config_in.phringe._director._planets[0].sky_coordinates[
                1, index_x[0].item(), index_y[0].item()].cpu().numpy()

            # Calculate threshold
            model = r_config_in.phringe.get_template_numpy(
                r_config_in.phringe.get_time_steps(as_numpy=True),
                r_config_in.phringe.get_wavelength_bin_centers(as_numpy=True),
                r_config_in.phringe.get_wavelength_bin_widths(as_numpy=True),
                x_coord,
                y_coord,
                r_config_in.scene.planets[0].spectral_flux_density.cpu().numpy()
            )
            model = model[0, :, :, 0, 0]

            if self.add:
                data = data + model
            else:
                data = data - model

            r_data_out.set_data(data)

        print('Done')
        return r_data_out

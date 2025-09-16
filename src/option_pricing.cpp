#include <cmath>
#include <random>
#include <algorithm>

double monte_carlo_call(double S0, double K, double r, double sigma, double T, int simulations) {
    std::mt19937 rng(std::random_device{}());
    std::normal_distribution<> norm(0.0, 1.0);

    double payoff_sum = 0.0;
    for (int i = 0; i < simulations; i++) {
        double ST = S0 * std::exp((r - 0.5*sigma*sigma)*T + sigma*std::sqrt(T)*norm(rng));
        payoff_sum += std::max(ST - K, 0.0);
    }
    return std::exp(-r*T) * payoff_sum / simulations;
}

double monte_carlo_put(double S0, double K, double r, double sigma, double T, int simulations) {
    std::mt19937 rng(std::random_device{}());
    std::normal_distribution<> norm(0.0, 1.0);

    double payoff_sum = 0.0;
    for (int i = 0; i < simulations; i++) {
        double ST = S0 * std::exp((r - 0.5*sigma*sigma)*T + sigma*std::sqrt(T)*norm(rng));
        payoff_sum += std::max(K - ST, 0.0);
    }
    return std::exp(-r*T) * payoff_sum / simulations;
}

#include <pybind11/pybind11.h>

namespace py = pybind11;

PYBIND11_MODULE(option_pricing, m) {
    m.def("monte_carlo_call", &monte_carlo_call, "Monte Carlo European Call Option");
    m.def("monte_carlo_put", &monte_carlo_put, "Monte Carlo European Put Option");
}
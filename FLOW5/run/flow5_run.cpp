#include <cctype>
#include <cmath>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#include <api.h>
#include <foil.h>
#include <objects2d.h>
#include <objects3d.h>
#include <panelanalysis.h>
#include <planeopp.h>
#include <planepolar.h>
#include <planetask.h>
#include <planexfl.h>
#include <stabderivatives.h>
#include <vector3d.h>

#include "nlohmann/json.hpp"

using json = nlohmann::json;

namespace {

double json_number(const json& j, double fallback = 0.0)
{
    if (j.is_number()) {
        return j.get<double>();
    }
    return fallback;
}

std::vector<double> json_double_array(const json& j)
{
    std::vector<double> out;
    if (!j.is_array()) {
        return out;
    }
    out.reserve(j.size());
    for (const auto& item : j) {
        out.push_back(json_number(item));
    }
    return out;
}

bool build_foils(const json& foils, std::string& err)
{
    if (!foils.is_array()) {
        err = "deck missing foils array";
        return false;
    }

    for (const auto& foil_json : foils) {
        if (!foil_json.contains("naca") || !foil_json.contains("name")) {
            err = "foil entry missing naca or name";
            return false;
        }

        const int naca = foil_json["naca"].get<int>();
        auto* pFoil = new Foil;
        if (!Objects2d::makeNacaFoil(pFoil, naca, 200)) {
            delete pFoil;
            err = "makeNacaFoil failed for NACA " + std::to_string(naca);
            return false;
        }
        pFoil->rePanel(150, 0.7);
        pFoil->setName(foil_json["name"].get<std::string>());
        Objects2d::insertThisFoil(pFoil);
    }

    return true;
}

WingXfl* add_wing_by_role(PlaneXfl* pPlane, const std::string& role)
{
    WingXfl* pWing = pPlane->addWing();
    if (role == "main") {
        pWing->makeDefaultWing();
    } else if (role == "elevator") {
        pWing->makeDefaultStab();
    } else if (role == "fin") {
        pWing->makeDefaultFin();
    } else {
        pWing->makeDefaultWing();
        pWing->setWingType(xfl::OtherWing);
    }
    return pWing;
}

bool configure_wing(WingXfl& wing, const json& wing_json, std::string& err)
{
    if (!wing_json.contains("sections") || !wing_json["sections"].is_array()) {
        err = "wing missing sections";
        return false;
    }

    const json& sections = wing_json["sections"];
    const int nSections = static_cast<int>(sections.size());
    if (nSections < 2) {
        err = "wing needs at least two sections";
        return false;
    }

    while (wing.nSections() < nSections) {
        wing.insertSection(wing.nSections() - 1);
    }

    const int nx = wing_json.contains("nx") ? wing_json["nx"].get<int>() : 10;

    for (int isec = 0; isec < nSections; ++isec) {
        const json& sec_json = sections[isec];
        WingSection& sec = wing.section(isec);

        if (!sec_json.contains("foil")) {
            err = "wing section missing foil";
            return false;
        }

        const std::string foil_name = sec_json["foil"].get<std::string>();
        sec.setFoilNames(foil_name, foil_name);
        sec.setNX(nx);
        sec.setXDistType(xfl::TANH);

        sec.setYPosition(json_number(sec_json["y_m"]));
        sec.setChord(json_number(sec_json["chord_m"]));
        sec.setXOffset(json_number(sec_json["x_offset_m"]));
        sec.setDihedral(json_number(sec_json["dihedral_deg"]));
        sec.setTwist(json_number(sec_json["twist_deg"]));

        if (sec_json.contains("ny")) {
            const int ny = sec_json["ny"].get<int>();
            if (ny > 0) {
                sec.setNY(ny);
                sec.setYDistType(xfl::UNIFORM);
            }
        }

        if (!sec_json.contains("te_flap_x")) {
            continue;
        }

        Foil* base = Objects2d::foil(foil_name);
        if (!base) {
            err = "te flap foil missing: " + foil_name;
            return false;
        }

        const double xhinge = json_number(sec_json["te_flap_x"]);
        const double angle = sec_json.contains("te_flap_deg")
            ? json_number(sec_json["te_flap_deg"])
            : 0.0;
        const bool antisym = sec_json.contains("te_flap_antisym")
            && sec_json["te_flap_antisym"].is_boolean()
            && sec_json["te_flap_antisym"].get<bool>();

        const std::string tag = wing.name() + "_s" + std::to_string(isec);
        const std::string right_name = tag + "_r";
        auto* right = new Foil(base);
        right->setName(right_name);
        right->setTEFlapData(true, xhinge, 0.0, angle);
        right->setFlaps();
        Objects2d::insertThisFoil(right);

        std::string left_name = right_name;
        if (antisym) {
            left_name = tag + "_l";
            auto* left = new Foil(base);
            left->setName(left_name);
            left->setTEFlapData(true, xhinge, 0.0, -angle);
            left->setFlaps();
            Objects2d::insertThisFoil(left);
        }
        sec.setFoilNames(left_name, right_name);
    }

    return true;
}

bool build_plane(const json& deck, PlaneXfl*& pPlaneOut, std::string& err)
{
    if (!deck.contains("wings") || !deck["wings"].is_array()) {
        err = "deck missing wings array";
        return false;
    }

    auto* pPlane = new PlaneXfl;
    pPlane->setName(deck.value("name", std::string("plane")));
    Objects3d::insertPlane(pPlane);

    for (const auto& wing_json : deck["wings"]) {
        if (!wing_json.contains("role")) {
            err = "wing missing role";
            return false;
        }

        const std::string role = wing_json["role"].get<std::string>();
        WingXfl* pWing = add_wing_by_role(pPlane, role);

        if (wing_json.contains("name")) {
            pWing->setName(wing_json["name"].get<std::string>());
        }

        if (!configure_wing(*pWing, wing_json, err)) {
            return false;
        }

        if (wing_json.contains("position_m") && wing_json["position_m"].is_array()
            && wing_json["position_m"].size() >= 3) {
            const auto& pos = wing_json["position_m"];
            pPlane->setWingPosition(
                pWing,
                json_number(pos[0]),
                json_number(pos[1]),
                json_number(pos[2]));
        }

        if (wing_json.contains("rx_deg")) {
            pPlane->setRxAngle(pWing, json_number(wing_json["rx_deg"]));
        }
        if (wing_json.contains("ry_deg")) {
            pPlane->setRyAngle(pWing, json_number(wing_json["ry_deg"]));
        }
        if (wing_json.contains("closed_inner")) {
            pWing->setClosedInnerSide(wing_json["closed_inner"].get<bool>());
        }
    }

    // Locked triple for Cessna native solve: makePlane(false, true, false) yields finite CL (no tri mesh).
    pPlane->setAutoInertia(false);
    pPlane->makePlane(false, true, false);

    pPlaneOut = pPlane;
    return true;
}

// polar.beta_deg is optional and absent means flow5's own default of 0. Absent
// and present have to be distinguishable, because the helper has no deck
// whitelist: an unknown key at any depth is silently ignored, so a typo would
// otherwise masquerade as beta = 0 and quietly void every lateral channel.
// That is why this checks the beta keys specifically rather than adding a
// general whitelist -- json_number() would also turn a non-numeric beta_deg
// into 0.0 without a word.
bool read_beta_spec(const json& polar_json, double& beta_deg, std::string& err)
{
    beta_deg = 0.0;
    for (const auto& item : polar_json.items()) {
        std::string lower_key = item.key();
        for (char& c : lower_key) {
            c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        }
        if (lower_key.find("beta") == std::string::npos) {
            continue;
        }
        if (item.key() != "beta_deg") {
            err = "polar key '" + item.key() + "' is not 'beta_deg'";
            return false;
        }
        if (!item.value().is_number()) {
            err = "polar beta_deg must be a number";
            return false;
        }
        beta_deg = item.value().get<double>();
    }
    return true;
}

// The stability scalars copied out of the library's StabDerivatives block, in
// the order they are written to the JSON. Deliberately NOT the whole block:
// Cma keeps its OLS key (the library's own Cma measures -1.0966 at the reference
// point, the OLS slope -1.5770), and the u-derivatives CXu/CZu/Cmu have no
// counterpart in the comparison tables. Every name here takes NO sign-map entry:
// PanelAnalysis::computeStabilityDerivatives projects onto the stability axes
// (panelanalysis.cpp:845-846, axes defined at :663-665), which is already
// Forward-Right-Down. Values are emitted raw, exactly as flow5 computes them.
struct StabDerivativeField {
    const char* name;
    double StabDerivatives::*member;
};

const std::vector<StabDerivativeField>& stab_derivative_fields()
{
    static const std::vector<StabDerivativeField> fields = {
        {"CXa", &StabDerivatives::CXa},
        {"CZa", &StabDerivatives::CZa},
        {"CYb", &StabDerivatives::CYb},
        {"CYp", &StabDerivatives::CYp},
        {"CYr", &StabDerivatives::CYr},
        {"Clb", &StabDerivatives::Clb},
        {"Clp", &StabDerivatives::Clp},
        {"Clr", &StabDerivatives::Clr},
        {"Cnb", &StabDerivatives::Cnb},
        {"Cnp", &StabDerivatives::Cnp},
        {"Cnr", &StabDerivatives::Cnr},
        {"XNP", &StabDerivatives::XNP},
    };
    return fields;
}

// Fills `out` with the reference operating point's stability derivatives. The
// reference point is the scheduled alpha closest to zero -- the trim the sweep
// is written around, and the point every measured value in this plan was taken
// at (alpha = 0 of the -4..+12 Cessna sweep).
//
// A non-finite derivative is a hard failure, not a 0.0: the locked thin-surface
// VLM2 triple used for the native solve is fragile, and a silent zero reads as a
// perfectly stable aircraft -- Cnb = 0.0 in particular is indistinguishable from
// "we computed this" at a glance in a coefficient table.
bool dump_reference_derivatives(
    PlaneTask* pPlaneTask, json& out, std::string& err)
{
    const std::vector<PlaneOpp*>& opps = pPlaneTask->planeOppList();
    if (opps.empty()) {
        err = "flow5 returned no operating points; PlaneTask::setKeepOpps(true) is required";
        return false;
    }

    const PlaneOpp* pRef = opps.front();
    for (const PlaneOpp* pOpp : opps) {
        if (std::abs(pOpp->alpha()) < std::abs(pRef->alpha())) {
            pRef = pOpp;
        }
    }

    for (const StabDerivativeField& field : stab_derivative_fields()) {
        const double value = pRef->m_SD.*(field.member);
        if (!std::isfinite(value)) {
            err = std::string("flow5 stability derivative ") + field.name
                + " is not finite (" + std::to_string(value)
                + ") at the reference operating point alpha = "
                + std::to_string(pRef->alpha()) + " deg";
            return false;
        }
        out[field.name] = value;
    }
    return true;
}

bool build_polar_and_run(
    PlaneXfl* pPlane,
    const json& polar_json,
    PlanePolar*& pPolarOut,
    json& derivatives,
    std::string& err)
{
    if (!polar_json.contains("alpha_deg")) {
        err = "polar missing alpha_deg";
        return false;
    }

    const std::vector<double> alpha_deg = json_double_array(polar_json["alpha_deg"]);
    if (alpha_deg.empty()) {
        err = "polar alpha_deg is empty";
        return false;
    }

    double beta_deg = 0.0;
    if (!read_beta_spec(polar_json, beta_deg, err)) {
        return false;
    }

    auto* pPlPolar = new PlanePolar;
    pPlPolar->setPlaneName(pPlane->name());

    // The only lever the library offers for a sideslip on a T1 polar: PlaneTask::run
    // reads betaSpec() at planetask.cpp:605 and rotates the mesh by it about the
    // CG (planetask.cpp:748), so the geometry stays put and only the flow yaws.
    pPlPolar->setBetaSpec(beta_deg);

    pPlPolar->setType(xfl::T1POLAR);
    pPlPolar->setAnalysisMethod(xfl::VLM2);
    pPlPolar->setThinSurfaces(true);
    pPlPolar->setViscous(false);

    pPlPolar->setVelocity(json_number(polar_json["qinf_mps"]));
    pPlPolar->setDensity(json_number(polar_json["density"]));
    pPlPolar->setViscosity(json_number(polar_json["viscosity"]));

    pPlPolar->setReferenceArea(json_number(polar_json["sref_m2"]));
    pPlPolar->setReferenceSpanLength(json_number(polar_json["bref_m"]));
    pPlPolar->setReferenceChordLength(json_number(polar_json["cref_m"]));

    if (polar_json.contains("cog_m") && polar_json["cog_m"].is_array()
        && polar_json["cog_m"].size() >= 3) {
        const auto& cog = polar_json["cog_m"];
        pPlPolar->setCoG(Vector3d{
            json_number(cog[0]),
            json_number(cog[1]),
            json_number(cog[2])});
    }

    pPlPolar->setMass(json_number(polar_json["mass_kg"]));
    pPlPolar->setAutoInertia(false);
    Objects3d::insertPlPolar(pPlPolar);

    auto* pPlaneTask = new PlaneTask;
    PanelAnalysis::setMaxThreadCount(1);
    pPlaneTask->outputToStdIO(false);
    pPlaneTask->setObjects(pPlane, pPlPolar);
    pPlaneTask->setComputeDerivatives(true);
    // Without this the library builds every StabDerivatives block and then throws
    // it away: PlaneTask::storePOpp only retains the opps when m_bKeepOpps is
    // set (planetask.cpp:2267-2271) and deletes them at :2273, so planeOppList()
    // would be empty and the dump below would silently emit nothing.
    pPlaneTask->setKeepOpps(true);
    pPlaneTask->setOppList(alpha_deg);
    pPlaneTask->run();

    if (pPlaneTask->hasErrors() || pPlPolar->dataSize() == 0) {
        err = "flow5 plane analysis failed";
        delete pPlaneTask;
        return false;
    }

    const bool dumped = dump_reference_derivatives(pPlaneTask, derivatives, err);

    delete pPlaneTask;
    if (!dumped) {
        return false;
    }
    pPolarOut = pPlPolar;
    return true;
}

json skeleton_output(const json& alpha_deg)
{
    const std::size_t n = alpha_deg.size();
    json out;
    out["alpha"] = alpha_deg;
    for (const char* key : {"beta", "CL", "CD", "CDvis", "CDind", "Cm",
                            "CY", "Cl", "Cn", "Cx", "Cz"}) {
        out[key] = json::array();
    }
    for (std::size_t i = 0; i < n; ++i) {
        for (const char* key : {"beta", "CL", "CD", "CDvis", "CDind", "Cm",
                                "CY", "Cl", "Cn", "Cx", "Cz"}) {
            out[key].push_back(0.0);
        }
    }
    out["CLa"] = 0;
    out["Cma"] = 0;
    for (const StabDerivativeField& field : stab_derivative_fields()) {
        out[field.name] = 0.0;
    }
    return out;
}

bool deck_has_native_geometry(const json& deck)
{
    return deck.contains("foils") && deck["foils"].is_array() && !deck["foils"].empty()
        && deck.contains("wings") && deck["wings"].is_array() && !deck["wings"].empty();
}

double ols_slope_rad(const std::vector<double>& alpha_deg, const std::vector<double>& y)
{
    const int n = static_cast<int>(alpha_deg.size());
    if (n < 2 || static_cast<int>(y.size()) != n) {
        return 0.0;
    }

    double sum_a = 0.0;
    double sum_y = 0.0;
    double sum_a2 = 0.0;
    double sum_ay = 0.0;
    for (int i = 0; i < n; ++i) {
        const double a = alpha_deg[i] * M_PI / 180.0;
        sum_a += a;
        sum_y += y[i];
        sum_a2 += a * a;
        sum_ay += a * y[i];
    }

    const double denom = n * sum_a2 - sum_a * sum_a;
    if (std::abs(denom) < 1e-12) {
        return 0.0;
    }
    return (n * sum_ay - sum_a * sum_y) / denom;
}

json polar_to_json(const PlanePolar* pPlPolar)
{
    json out;
    out["alpha"] = json::array();
    out["beta"] = json::array();
    out["CL"] = json::array();
    out["CD"] = json::array();
    out["CDvis"] = json::array();
    out["CDind"] = json::array();
    out["Cm"] = json::array();
    out["CY"] = json::array();
    out["Cl"] = json::array();
    out["Cn"] = json::array();
    out["Cx"] = json::array();
    out["Cz"] = json::array();

    std::vector<double> alpha_deg;
    std::vector<double> cl;
    std::vector<double> cm;

    const int n = pPlPolar->dataSize();
    alpha_deg.reserve(n);
    cl.reserve(n);
    cm.reserve(n);
    for (int i = 0; i < n; ++i) {
        const double alpha = pPlPolar->getVariable(1, i);
        const double cl_i = pPlPolar->getVariable(4, i);
        const double cd_i = pPlPolar->getVariable(5, i);
        const double cm_i = pPlPolar->getVariable(9, i);
        out["alpha"].push_back(alpha);
        out["beta"].push_back(pPlPolar->getVariable(2, i));
        out["CL"].push_back(cl_i);
        out["CD"].push_back(cd_i);
        out["CDvis"].push_back(pPlPolar->getVariable(6, i));
        out["CDind"].push_back(pPlPolar->getVariable(7, i));
        out["Cm"].push_back(cm_i);
        out["CY"].push_back(pPlPolar->getVariable(8, i));
        out["Cl"].push_back(pPlPolar->getVariable(12, i));
        out["Cn"].push_back(pPlPolar->getVariable(13, i));
        out["Cx"].push_back(pPlPolar->getVariable(57, i));
        out["Cz"].push_back(pPlPolar->getVariable(58, i));
        alpha_deg.push_back(alpha);
        cl.push_back(cl_i);
        cm.push_back(cm_i);
    }

    out["CLa"] = ols_slope_rad(alpha_deg, cl);
    out["Cma"] = ols_slope_rad(alpha_deg, cm);
    return out;
}

} // namespace

int main(int argc, char* argv[])
{
    if (argc != 3 || std::string(argv[1]) != "--deck") {
        std::cerr << "usage: flow5_run --deck FILE\n";
        return 2;
    }

    const std::string deck_path = argv[2];
    std::ifstream in(deck_path);
    if (!in) {
        std::cerr << "cannot open deck file: " << deck_path << '\n';
        return 1;
    }

    json deck;
    try {
        in >> deck;
    } catch (const json::parse_error&) {
        std::cerr << "invalid JSON deck\n";
        return 1;
    }

    if (!deck.contains("polar") || !deck["polar"].contains("alpha_deg")
        || !deck["polar"]["alpha_deg"].is_array()) {
        std::cerr << "deck missing polar.alpha_deg\n";
        return 1;
    }

    const json& alpha_deg = deck["polar"]["alpha_deg"];
    if (!deck_has_native_geometry(deck)) {
        std::cout << skeleton_output(alpha_deg).dump() << '\n';
        return 0;
    }

    std::string err;
    if (!build_foils(deck["foils"], err)) {
        std::cerr << err << '\n';
        globals::deleteObjects();
        return 1;
    }

    PlaneXfl* pPlane = nullptr;
    if (!build_plane(deck, pPlane, err)) {
        std::cerr << err << '\n';
        globals::deleteObjects();
        return 1;
    }

    PlanePolar* pPlPolar = nullptr;
    json derivatives;
    if (!build_polar_and_run(pPlane, deck["polar"], pPlPolar, derivatives, err)) {
        std::cerr << err << '\n';
        globals::deleteObjects();
        return 1;
    }

    json out = polar_to_json(pPlPolar);
    out.update(derivatives);
    std::cout << out.dump() << '\n';

    globals::deleteObjects();
    return 0;
}

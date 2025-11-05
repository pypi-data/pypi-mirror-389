{
  description = "Fluidattacks ETLs success indicators";

  inputs = {
    observes_flake_builder = {
      url =
        "github:fluidattacks/universe/41ea58333c8fbb68499a470444b6619023f74a2b?shallow=1&dir=observes/common/std_flake_2";
    };
  };

  outputs = { self, ... }@inputs:
    let
      build_args = { system, python_version, nixpkgs, builders, scripts }:
        import ./build {
          inherit nixpkgs builders scripts;
          src = import ./build/filter.nix nixpkgs.nix-filter self;
        };
    in { packages = inputs.observes_flake_builder.outputs.build build_args; };
}
